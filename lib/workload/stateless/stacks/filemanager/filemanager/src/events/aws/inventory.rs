//! Handles S3 Inventory reports and converts them to events that can be ingested.
//!

use arrow::array::RecordBatch;
use arrow::error::ArrowError;
use arrow_json::ArrayWriter;
use aws_arn::known::Service;
use aws_arn::ResourceName;
use aws_sdk_s3::types::InventoryFormat;
use chrono::{DateTime, NaiveDateTime, Utc};
use csv::{ReaderBuilder, StringRecord, Trim};
use flate2::read::MultiGzDecoder;
use futures::future::join_all;
use futures::{Stream, TryStreamExt};
use orc_rust::error::OrcError;
use orc_rust::ArrowReaderBuilder;
use parquet::arrow::ParquetRecordBatchStreamBuilder;
use parquet::errors::ParquetError;
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::from_slice;
use serde_with::{serde_as, DisplayFromStr};
use std::hash::{Hash, Hasher};
use std::io::{BufReader, Cursor, Read};
use std::result;

use crate::clients::aws::s3::Client;
use crate::database::entities::sea_orm_active_enums::Reason;
use crate::error::Error::S3Error;
use crate::error::{Error, Result};
use crate::events::aws::message::{default_version_id, quote_e_tag, EventType::Created};
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::uuid::UuidGenerator;

const DEFAULT_CSV_MANIFEST: &str =
    "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, LastModifiedDate, ETag, StorageClass";

/// Represents an S3 inventory including associated inventory fetching and parsing logic.
#[derive(Debug)]
pub struct Inventory {
    client: Client,
}

impl Inventory {
    /// Create a new inventory.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new inventory with a default s3 client.
    pub async fn with_defaults() -> Self {
        Self::new(Client::with_defaults().await)
    }

    /// Trim ascii whitespace from byte data.
    /// TODO, replace this with std function once stable:
    /// https://github.com/rust-lang/rust/issues/94035
    fn trim_whitespace(bytes: &[u8]) -> &[u8] {
        let end_pos = match bytes.iter().rposition(|char| !char.is_ascii_whitespace()) {
            Some(i) => i,
            None => bytes.len(),
        };

        &bytes[..=end_pos]
    }

    /// Parse a CSV manifest file into records.
    pub async fn parse_csv(&self, schema: Option<&str>, body: &[u8]) -> Result<Vec<Record>> {
        let mut inventory_bytes = vec![];
        MultiGzDecoder::new(BufReader::new(body))
            .read_to_end(&mut inventory_bytes)
            .map_err(|err| S3Error(format!("decompressing CSV: {}", err)))?;

        // AWS seems to return extra newlines at the end of the CSV, so we remove these
        let inventory_bytes = Self::trim_whitespace(inventory_bytes.as_slice());

        let reader_builder = || {
            let mut builder = ReaderBuilder::new();
            builder.trim(Trim::All);
            builder
        };

        let set_headers = |csv: &mut csv::Reader<&[u8]>, header: &[u8]| {
            let mut header_record = StringRecord::new();
            reader_builder()
                .has_headers(false)
                .from_reader(header)
                .read_record(&mut header_record)?;

            csv.set_headers(header_record);

            Ok::<_, Error>(())
        };

        let mut csv = reader_builder().from_reader(inventory_bytes);
        if let Some(schema) = schema {
            // If a schema is available, use that.
            set_headers(&mut csv, schema.as_bytes())?;
        } else {
            // If not, try to parse the csv with headers, otherwise fallback to a default schema.
            let mut header_reader = reader_builder().from_reader(inventory_bytes);
            let mut iter = header_reader.deserialize::<Record>();
            if let Some(Err(_)) = iter.next() {
                // Failed to read a header row, fallback on default schema.
                set_headers(&mut csv, DEFAULT_CSV_MANIFEST.as_bytes())?;
            }
        }

        Ok(csv.deserialize().collect::<result::Result<_, _>>()?)
    }

    /// Parse an arrow record batch from an incoming stream into messages for ingestion.
    pub async fn parse_record_batch(
        &self,
        stream: impl Stream<Item = result::Result<RecordBatch, ArrowError>> + Unpin,
    ) -> Result<Vec<Record>> {
        let batches = stream.try_collect::<Vec<_>>().await?;

        let buf = Vec::new();
        let mut writer = ArrayWriter::new(buf);
        writer.write_batches(&batches.iter().collect::<Vec<_>>())?;
        writer.finish()?;

        let buf = writer.into_inner();

        // This is definitely not the fastest solution, but it is by far the simplest in-code solution
        // (saves ~200 lines of very repetitive code) with the least dependencies.
        // See some speed comparisons here:
        // https://github.com/chmp/serde_arrow?tab=readme-ov-file#related-packages--performance
        //
        // A more performant solution could involve using:
        // https://github.com/Swoorup/arrow-convert
        // This is should be similar to arrow2_convert::TryIntoArrow in the above performance graph,
        // as it is a port of arrow2_convert with arrow-rs as the dependency.
        from_slice::<Vec<Record>>(buf.as_slice())
            .map_err(|err| S3Error(format!("failed to deserialize json from arrow: {}", err)))
    }

    /// Parse a parquet manifest file into records.
    pub async fn parse_parquet(&self, body: Vec<u8>) -> Result<Vec<Record>> {
        let reader = ParquetRecordBatchStreamBuilder::new(Cursor::new(body))
            .await?
            .build()?
            .map_err(ArrowError::from);

        self.parse_record_batch(reader).await
    }

    /// Parse an ORC manifest file into records.
    pub async fn parse_orc(&self, body: Vec<u8>) -> Result<Vec<Record>> {
        let reader = ArrowReaderBuilder::try_new_async(Cursor::new(body))
            .await?
            .build_async();

        self.parse_record_batch(reader).await
    }

    /// Call `GetObject` on the key and bucket, returning the byte data of the response.
    async fn get_object_bytes<K: AsRef<str>>(&self, key: K, bucket: K) -> Result<Vec<u8>> {
        Ok(self
            .client
            .get_object(key.as_ref(), bucket.as_ref(), default_version_id().as_ref())
            .await
            .map_err(|err| S3Error(err.to_string()))?
            .body
            .collect()
            .await
            .map_err(|err| S3Error(err.to_string()))?
            .to_vec())
    }

    /// Verify the md5sum of the data returning an error if there is a mismatch.
    fn verify_md5<T: AsRef<[u8]>>(data: T, verify_with: T) -> Result<()> {
        if md5::compute(data).0
            != hex::decode(&verify_with)
                .map_err(|err| S3Error(format!("decoding hex string: {}", err)))?
                .as_slice()
        {
            return Err(S3Error(
                "mismatched MD5 checksums in inventory manifest".to_string(),
            ));
        }

        Ok(())
    }

    /// Parse records from a bucket and key containing an S3 inventory manifest file. This can either
    /// be a manifest.json file or a manifest.checksum.
    pub async fn parse_manifest_key<K: AsRef<str>>(
        &self,
        key: K,
        bucket: K,
    ) -> Result<Vec<Record>> {
        let data = self.get_object_bytes(key.as_ref(), bucket.as_ref()).await?;

        let try_json = from_slice(data.as_slice());

        if try_json.is_err() {
            // If this is an error, assume that this data represents a checksum.
            let mut manifest_key = key.as_ref().to_string();
            manifest_key.truncate(
                manifest_key
                    .rfind('.')
                    .unwrap_or_else(|| key.as_ref().len()),
            );

            let manifest = self
                .get_object_bytes(
                    format!("{}.json", manifest_key.as_str()).as_str(),
                    bucket.as_ref(),
                )
                .await?;

            Self::verify_md5(manifest.as_slice(), Self::trim_whitespace(data.as_slice()))?;

            self.parse_manifest(from_slice(manifest.as_slice())?).await
        } else {
            // Otherwise return the JSON manifest.
            self.parse_manifest(try_json?).await
        }
    }

    /// Parse records based on the inventory format.
    pub async fn records_from_format(
        &self,
        format: &InventoryFormat,
        body: Vec<u8>,
        schema: Option<&str>,
    ) -> Result<Vec<Record>> {
        match format {
            InventoryFormat::Csv => self.parse_csv(schema, body.as_slice()).await,
            InventoryFormat::Parquet => self.parse_parquet(body).await,
            InventoryFormat::Orc => self.parse_orc(body).await,
            _ => Err(S3Error("unsupported manifest file type".to_string())),
        }
    }

    /// Parse a manifest into records.
    pub async fn parse_manifest(&self, manifest: Manifest) -> Result<Vec<Record>> {
        let arn: result::Result<ResourceName, _> = manifest.destination_bucket.parse();

        let bucket = match arn {
            // Proper arn, parse out the bucket.
            Ok(arn) => {
                if arn.service != Service::S3.into() {
                    return Err(S3Error("destination bucket ARN is not S3".to_string()));
                }
                arn.resource.to_string()
            }
            // Ok, try and use the destination bucket as a string directly.
            Err(_) => manifest.destination_bucket,
        };

        // TODO: consider streaming a file and reading records without placing them into memory first.
        let inventories = join_all(manifest.files.iter().map(|file| async {
            let body = self.get_object_bytes(&file.key, &bucket).await?;

            if let Some(checksum) = &file.md5_checksum {
                Self::verify_md5(body.as_slice(), checksum.as_bytes())?;
            }

            self.records_from_format(&manifest.file_format, body, manifest.file_schema.as_deref())
                .await
        }))
        .await
        .into_iter()
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .flatten()
        .collect();

        Ok(inventories)
    }
}

impl From<csv::Error> for Error {
    fn from(error: csv::Error) -> Self {
        S3Error(error.to_string())
    }
}

impl From<ParquetError> for Error {
    fn from(error: ParquetError) -> Self {
        S3Error(error.to_string())
    }
}

impl From<ArrowError> for Error {
    fn from(error: ArrowError) -> Self {
        S3Error(error.to_string())
    }
}

impl From<OrcError> for Error {
    fn from(error: OrcError) -> Self {
        S3Error(error.to_string())
    }
}

/// An S3 inventory record.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq, Clone)]
pub struct Record {
    #[serde(alias = "Bucket")]
    bucket: String,
    #[serde(alias = "Key")]
    key: String,
    #[serde(alias = "VersionId")]
    version_id: Option<String>,
    #[serde(alias = "IsDeleteMarker")]
    is_delete_marker: Option<bool>,
    #[serde(alias = "Size")]
    size: Option<i64>,
    #[serde(
        alias = "LastModifiedDate",
        deserialize_with = "deserialize_native_utc"
    )]
    last_modified_date: Option<DateTime<Utc>>,
    #[serde(alias = "ETag")]
    e_tag: Option<String>,
    #[serde(alias = "StorageClass")]
    storage_class: Option<StorageClass>,
}

impl Record {
    /// Create a new record builder.
    pub fn builder() -> RecordBuilder {
        RecordBuilder::default()
    }

    /// Set the version id.
    pub fn set_version_id(mut self, version_id: String) -> Self {
        self.version_id = Some(version_id);
        self
    }

    /// Set the delete marker.
    pub fn set_is_delete_marker(mut self, is_delete_marker: bool) -> Self {
        self.is_delete_marker = Some(is_delete_marker);
        self
    }
}

/// A builder for an S3 inventory record.
#[derive(Debug, Default)]
pub struct RecordBuilder {
    version_id: Option<String>,
    size: Option<i64>,
    last_modified_date: Option<DateTime<Utc>>,
    e_tag: Option<String>,
    storage_class: Option<StorageClass>,
    is_delete_marker: Option<bool>,
}

impl RecordBuilder {
    /// Add a version id to the record.
    pub fn with_version_id(mut self, version_id: String) -> Self {
        self.version_id = Some(version_id);
        self
    }

    /// Add a size to the record.
    pub fn with_size(mut self, size: i64) -> Self {
        self.size = Some(size);
        self
    }

    /// Add a last modified date to the record.
    pub fn with_last_modified_date(mut self, last_modified_date: DateTime<Utc>) -> Self {
        self.last_modified_date = Some(last_modified_date);
        self
    }

    /// Add an e-tag to the record.
    pub fn with_e_tag(mut self, e_tag: String) -> Self {
        self.e_tag = Some(e_tag);
        self
    }

    /// Add a storage class to the record.
    pub fn with_storage_class(mut self, storage_class: StorageClass) -> Self {
        self.storage_class = Some(storage_class);
        self
    }

    /// Add a delete marker to the record.
    pub fn with_delete_marker(mut self, is_delete_marker: Option<bool>) -> Self {
        self.is_delete_marker = is_delete_marker;
        self
    }

    /// Build the record.
    pub fn build(self, bucket: String, key: String) -> Record {
        Record {
            bucket,
            key,
            version_id: self.version_id,
            size: self.size,
            last_modified_date: self.last_modified_date,
            e_tag: self.e_tag,
            storage_class: self.storage_class,
            is_delete_marker: self.is_delete_marker,
        }
    }
}

/// Deserializes into a DateTime<Utc>, or a NativeDateTime which is converted into a DateTime<Utc>
/// that is assumed to be native to Utc.
///
///
/// Note, AWS returns a LastModifiedDate which seems to be in UTC. However, it uses the incorrect
/// timestamp datatype for ORC/Parquet, which doesn't include a timezone (and hence is assumed to
/// be in local time, which can't be parsed as a DateTime<Utc>).
///
/// This is likely a bug in AWS, so we fix it here and ensure that the timezone component is
/// present.
pub fn deserialize_native_utc<'de, D>(
    deserializer: D,
) -> result::Result<Option<DateTime<Utc>>, D::Error>
where
    D: Deserializer<'de>,
{
    // Throw-away enum, first try to deserialize as a DateTime<Utc>, then try a NativeDateTime.
    #[derive(Deserialize)]
    #[serde(untagged)]
    enum Date {
        Utc(DateTime<Utc>),
        Native(NaiveDateTime),
    }

    Ok(
        Option::<Date>::deserialize(deserializer)?.map(|datetime| match datetime {
            Date::Utc(utc) => utc,
            Date::Native(native) => native.and_utc(),
        }),
    )
}

/// The manifest format for an inventory.
#[serde_as]
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Manifest {
    destination_bucket: String,
    #[serde_as(as = "DisplayFromStr")]
    file_format: InventoryFormat,
    file_schema: Option<String>,
    files: Vec<File>,
}

impl Manifest {
    /// Create a new manifest.
    pub fn new(
        destination_bucket: String,
        file_format: InventoryFormat,
        file_schema: Option<String>,
        files: Vec<File>,
    ) -> Self {
        Self {
            destination_bucket,
            file_format,
            file_schema,
            files,
        }
    }
}

/// The files inside the manifest.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct File {
    key: String,
    #[serde(rename = "MD5checksum")]
    md5_checksum: Option<String>,
}

impl File {
    /// Create a new file
    pub fn new(key: String, md5_checksum: Option<String>) -> Self {
        Self { key, md5_checksum }
    }
}

impl From<Vec<Record>> for FlatS3EventMessages {
    fn from(records: Vec<Record>) -> Self {
        Self(records.into_iter().map(|record| record.into()).collect())
    }
}

impl From<Record> for FlatS3EventMessages {
    fn from(record: Record) -> Self {
        Self(vec![record.into()])
    }
}

impl From<Record> for FlatS3EventMessage {
    fn from(record: Record) -> Self {
        let Record {
            bucket,
            key,
            version_id,
            is_delete_marker,
            size,
            last_modified_date,
            e_tag,
            storage_class,
        } = record;

        Self {
            s3_object_id: UuidGenerator::generate(),
            // We don't know when this object was created so there is no event time.
            event_time: None,
            bucket,
            key,
            size,
            e_tag: e_tag.map(quote_e_tag),
            // Set this to null to generate a sequencer.
            sequencer: None,
            version_id: version_id.unwrap_or_else(default_version_id),
            storage_class,
            last_modified_date,
            sha256: None,
            // Anything in an inventory report is always a created event.
            event_type: Created,
            is_delete_marker: is_delete_marker.unwrap_or_default(),
            reason: Reason::Crawl,
            archive_status: None,
            // This will also represent the current state since it is a created event.
            is_current_state: true,
            ingest_id: None,
            attributes: None,
            number_duplicate_events: 0,
            number_reordered: 0,
        }
    }
}

/// A wrapper around event messages to allow for calculating a diff compared to the database
/// state. Checks for equality using the bucket, key and version_id.
#[derive(Debug, Eq, Clone)]
pub struct DiffMessages(FlatS3EventMessage);

impl Hash for DiffMessages {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.bucket.hash(state);
        self.0.key.hash(state);
        self.0.version_id.hash(state);
    }
}

impl PartialEq for DiffMessages {
    fn eq(&self, other: &Self) -> bool {
        self.0.bucket == other.0.bucket
            && self.0.key == other.0.key
            && self.0.version_id == other.0.version_id
    }
}

impl From<FlatS3EventMessages> for Vec<DiffMessages> {
    fn from(value: FlatS3EventMessages) -> Self {
        value.0.into_iter().map(DiffMessages).collect()
    }
}

impl From<Vec<DiffMessages>> for FlatS3EventMessages {
    fn from(value: Vec<DiffMessages>) -> Self {
        Self(value.into_iter().map(|diff| diff.0).collect())
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use std::collections::HashSet;

    use crate::events::aws::collecter::tests::mock_s3;
    use crate::events::aws::inventory::Manifest;
    use crate::events::aws::tests::EXPECTED_E_TAG;
    use aws_sdk_s3::operation::get_object::GetObjectOutput;
    use aws_sdk_s3::primitives::ByteStream;
    use aws_smithy_mocks_experimental::{mock, Rule};
    use chrono::Days;
    use flate2::read::GzEncoder;
    use serde_json::json;
    use serde_json::Value;

    use super::*;

    const CSV_MANIFEST_SCHEMA: &str = "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner";

    const MANIFEST_KEY: &str = "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce";
    pub(crate) const MANIFEST_BUCKET: &str = "example-inventory-destination-bucket";
    const EXPECTED_CHECKSUM: &str = "f11166069f1990abeb9c97ace9cdfabc"; // pragma: allowlist secret

    pub(crate) const EXPECTED_E_TAG_KEY_2: &str = "d8e8fca2dc0f896fd7cb4cb0031ba249"; // pragma: allowlist secret
    pub(crate) const EXPECTED_QUOTED_E_TAG_KEY_2: &str = "\"d8e8fca2dc0f896fd7cb4cb0031ba249\""; // pragma: allowlist secret
    pub(crate) const EXPECTED_LAST_MODIFIED_ONE: &str = "2024-04-22T01:11:06.000Z";
    pub(crate) const EXPECTED_LAST_MODIFIED_TWO: &str = "2024-04-22T01:13:28.000Z";
    pub(crate) const EXPECTED_LAST_MODIFIED_THREE: &str = "2024-04-22T01:14:53.000Z";

    #[test]
    fn diff_messages() {
        let database_records = vec![
            FlatS3EventMessage {
                bucket: "bucket".to_string(),
                key: "key".to_string(),
                version_id: "version".to_string(),
                // Other fields shouldn't affect this.
                last_modified_date: Some(DateTime::default()),
                ..Default::default()
            },
            FlatS3EventMessage {
                bucket: "bucket".to_string(),
                key: "key1".to_string(),
                version_id: "version".to_string(),
                ..Default::default()
            },
        ];
        let inventory_records = vec![
            FlatS3EventMessage {
                bucket: "bucket".to_string(),
                key: "key".to_string(),
                version_id: "version".to_string(),
                last_modified_date: Some(
                    DateTime::default().checked_add_days(Days::new(1)).unwrap(),
                ),
                ..Default::default()
            },
            FlatS3EventMessage {
                bucket: "bucket".to_string(),
                key: "key2".to_string(),
                version_id: "version".to_string(),
                ..Default::default()
            },
        ];

        let inventory_records: HashSet<DiffMessages> = HashSet::from_iter(
            Vec::<DiffMessages>::from(FlatS3EventMessages(inventory_records)),
        );
        let database_records: HashSet<DiffMessages> = HashSet::from_iter(
            Vec::<DiffMessages>::from(FlatS3EventMessages(database_records)),
        );

        let diff = &inventory_records - &database_records;
        let expected = HashSet::from_iter(vec![DiffMessages(FlatS3EventMessage {
            bucket: "bucket".to_string(),
            key: "key2".to_string(),
            version_id: "version".to_string(),
            ..Default::default()
        })]);

        assert_eq!(diff, expected);
    }

    #[tokio::test]
    async fn parse_csv_manifest_from_checksum() {
        let (_, checksum) = test_csv_manifest(None, csv_data_empty_string(), &[]);

        let bytes = csv_manifest_to_json(checksum);
        let checksum = format!("{}\n", hex::encode(md5::compute(bytes.as_slice()).0))
            .as_bytes()
            .to_vec();
        let (client, _) = test_csv_manifest(
            None,
            csv_data_empty_string(),
            &[
                set_client_manifest_expectations(bytes),
                mock!(aws_sdk_s3::Client::get_object)
                    .match_requests(move |req| {
                        req.key() == Some("manifest.checksum")
                            && req.bucket() == Some(MANIFEST_BUCKET)
                            && req.version_id().is_none()
                    })
                    .then_output(move || {
                        GetObjectOutput::builder()
                            .body(ByteStream::from(checksum.clone()))
                            .build()
                    }),
            ],
        );

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest_key("manifest.checksum", MANIFEST_BUCKET)
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[tokio::test]
    async fn parse_csv_manifest_from_key() {
        let client = csv_manifest_from_key_expectations();

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest_key("manifest.json", MANIFEST_BUCKET)
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[tokio::test]
    async fn parse_csv_manifest() {
        assert_csv_with(
            None,
            csv_data_empty_string(),
            Some(CSV_MANIFEST_SCHEMA.to_string()),
            true,
        )
        .await;
        assert_csv_with(
            None,
            csv_data_missing(),
            Some(CSV_MANIFEST_SCHEMA.to_string()),
            true,
        )
        .await;
    }

    #[tokio::test]
    async fn parse_csv_manifest_no_checksum() {
        assert_csv_with(
            None,
            csv_data_empty_string(),
            Some(CSV_MANIFEST_SCHEMA.to_string()),
            false,
        )
        .await;
        assert_csv_with(
            None,
            csv_data_missing(),
            Some(CSV_MANIFEST_SCHEMA.to_string()),
            false,
        )
        .await;
    }

    #[tokio::test]
    async fn parse_csv_manifest_with_headers() {
        assert_csv_with(
            Some(CSV_MANIFEST_SCHEMA),
            csv_data_empty_string(),
            None,
            true,
        )
        .await;
        assert_csv_with(Some(CSV_MANIFEST_SCHEMA), csv_data_missing(), None, true).await;
    }

    #[tokio::test]
    async fn parse_csv_manifest_default_schema() {
        assert_csv_with(None, csv_data_empty_string(), None, true).await;
        assert_csv_with(None, csv_data_missing(), None, true).await;
    }

    #[tokio::test]
    async fn parse_csv_manifest_different_schema() {
        let data = concat!(
            r#""0","bucket","inventory_test/","","true","false","2024-04-22T01:11:06.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""0","bucket","inventory_test/key1","","true","false","2024-04-22T01:13:28.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""5","bucket","inventory_test/key2","","true","false","2024-04-22T01:14:53.000Z","d8e8fca2dc0f896fd7cb4cb0031ba249","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n\n"
        );

        let mut bytes = vec![];
        let mut reader = GzEncoder::new(data.as_bytes(), Default::default());
        reader.read_to_end(&mut bytes).unwrap();

        let checksum = hex::encode(md5::compute(bytes.as_slice()).0);
        let client = set_client_expectations(&InventoryFormat::Csv, bytes, &[]);

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest(expected_manifest(
                Some(
                    "Size, Bucket, Key, VersionId, IsLatest, IsDeleteMarker, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner"
                        .to_string(),
                ),
                InventoryFormat::Csv,
                Some(checksum),
            ))
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[test]
    fn deserialize_csv_manifest() {
        let manifest = expected_json_manifest(&InventoryFormat::Csv);

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(
            result,
            expected_csv_manifest(
                Some(EXPECTED_CHECKSUM.to_string()),
                Some(CSV_MANIFEST_SCHEMA.to_string())
            )
        );
    }

    #[test]
    fn deserialize_orc_manifest() {
        let manifest = expected_json_manifest(&InventoryFormat::Orc);

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(result, expected_orc_manifest(EXPECTED_CHECKSUM.to_string()));
    }

    #[test]
    fn deserialize_parquet_manifest() {
        let manifest = expected_json_manifest(&InventoryFormat::Parquet);

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(
            result,
            expected_parquet_manifest(EXPECTED_CHECKSUM.to_string())
        );
    }

    async fn assert_csv_with(
        headers: Option<&str>,
        data: String,
        schema: Option<String>,
        use_checksum: bool,
    ) {
        let (client, checksum) = test_csv_manifest(headers, data, &[]);

        let checksum = if use_checksum { Some(checksum) } else { None };

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest(expected_csv_manifest(checksum, schema))
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    pub(crate) fn csv_manifest_from_key_expectations() -> Client {
        let (_, checksum) = test_csv_manifest(None, csv_data_empty_string(), &[]);

        let bytes = csv_manifest_to_json(checksum);
        test_csv_manifest(
            None,
            csv_data_empty_string(),
            &[set_client_manifest_expectations(bytes)],
        )
        .0
    }

    fn csv_manifest_to_json(checksum: String) -> Vec<u8> {
        serde_json::to_vec_pretty(&expected_csv_manifest(
            Some(checksum),
            Some(CSV_MANIFEST_SCHEMA.to_string()),
        ))
        .unwrap()
    }

    fn set_client_manifest_expectations(data: Vec<u8>) -> Rule {
        mock!(aws_sdk_s3::Client::get_object)
            .match_requests(move |req| {
                req.key() == Some("manifest.json")
                    && req.bucket() == Some(MANIFEST_BUCKET)
                    && req.version_id().is_none()
            })
            .then_output(move || {
                GetObjectOutput::builder()
                    .body(ByteStream::from(data.clone()))
                    .build()
            })
    }

    fn csv_data_empty_string() -> String {
        concat!(
            r#""bucket","inventory_test/","","true","false","0","2024-04-22T01:11:06.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key1","","true","false","0","2024-04-22T01:13:28.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key2","","true","false","5","2024-04-22T01:14:53.000Z","d8e8fca2dc0f896fd7cb4cb0031ba249","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n\n"
        )
        .to_string()
    }

    fn csv_data_missing() -> String {
        concat!(
            r#""bucket","inventory_test/",,"true","false","0","2024-04-22T01:11:06.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false",,"SSE-S3",,,,,"DISABLED",,"e30K","#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key1",,"true","false","0","2024-04-22T01:13:28.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false",,"SSE-S3",,,,,"DISABLED",,"e30K","#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key2",,"true","false","5","2024-04-22T01:14:53.000Z","d8e8fca2dc0f896fd7cb4cb0031ba249","STANDARD","false",,"SSE-S3",,,,,"DISABLED",,"e30K","#, // pragma: allowlist secret
            "\n\n"
        )
        .to_string()
    }

    fn test_csv_manifest(
        headers: Option<&str>,
        mut data: String,
        expectations: &[Rule],
    ) -> (Client, String) {
        if let Some(headers) = headers {
            data = format!("{}\n{}", headers, data);
        }

        let mut bytes = vec![];
        let mut reader = GzEncoder::new(data.as_bytes(), Default::default());
        reader.read_to_end(&mut bytes).unwrap();

        let checksum = hex::encode(md5::compute(bytes.as_slice()).0);
        let client = set_client_expectations(&InventoryFormat::Csv, bytes, expectations);

        (client, checksum)
    }

    fn set_client_expectations(
        file_format: &InventoryFormat,
        data: Vec<u8>,
        expectations: &[Rule],
    ) -> Client {
        let ending = ending_from_format(file_format).to_string();

        mock_s3(
            &[
                &[mock!(aws_sdk_s3::Client::get_object)
                    .match_requests(move |req| {
                        req.key() == Some(&format!("{}{}", MANIFEST_KEY, ending))
                            && req.bucket() == Some(MANIFEST_BUCKET)
                            && req.version_id().is_none()
                    })
                    .then_output(move || {
                        GetObjectOutput::builder()
                            .body(ByteStream::from(data.clone()))
                            .build()
                    })],
                expectations,
            ]
            .concat(),
        )
    }

    fn expected_json_manifest(format: &InventoryFormat) -> Value {
        // Taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest
        let mut value = json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": format!("arn:aws:s3:::{}", MANIFEST_BUCKET),
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": format.as_str(),
            "files": [{
                "key": format!("{}{}", MANIFEST_KEY, ending_from_format(format)),
                "size": 2147483647,
                "MD5checksum": EXPECTED_CHECKSUM
            }]
        });

        // Orc and Parquet manifest is ignored anyway.
        if let InventoryFormat::Csv = format {
            value["fileSchema"] = Value::String(CSV_MANIFEST_SCHEMA.to_string());
        };

        value
    }

    fn expected_manifest(
        file_schema: Option<String>,
        file_format: InventoryFormat,
        md5_checksum: Option<String>,
    ) -> Manifest {
        let ending = ending_from_format(&file_format);

        Manifest {
            destination_bucket: format!("arn:aws:s3:::{}", MANIFEST_BUCKET),
            file_format: file_format.clone(),
            file_schema,
            files: vec![File {
                key: format!("{}{}", MANIFEST_KEY, ending),
                md5_checksum,
            }],
        }
    }

    fn ending_from_format(file_format: &InventoryFormat) -> &str {
        match file_format {
            InventoryFormat::Csv => ".csv.gz",
            InventoryFormat::Orc => ".orc",
            InventoryFormat::Parquet => ".parquet",
            _ => "",
        }
    }

    fn expected_orc_manifest(checksum: String) -> Manifest {
        expected_manifest(None, InventoryFormat::Orc, Some(checksum))
    }

    fn expected_parquet_manifest(checksum: String) -> Manifest {
        expected_manifest(None, InventoryFormat::Parquet, Some(checksum))
    }

    fn expected_csv_manifest(checksum: Option<String>, schema: Option<String>) -> Manifest {
        expected_manifest(schema, InventoryFormat::Csv, checksum)
    }

    fn assert_csv_records(result: &[Record]) {
        assert_eq!(
            result,
            vec![
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/".to_string(),
                    version_id: None,
                    is_delete_marker: Some(false),
                    size: Some(0),
                    last_modified_date: Some(EXPECTED_LAST_MODIFIED_ONE.parse().unwrap()),
                    e_tag: Some(EXPECTED_E_TAG.to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/key1".to_string(),
                    version_id: None,
                    is_delete_marker: Some(false),
                    size: Some(0),
                    last_modified_date: Some(EXPECTED_LAST_MODIFIED_TWO.parse().unwrap()),
                    e_tag: Some(EXPECTED_E_TAG.to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/key2".to_string(),
                    version_id: None,
                    is_delete_marker: Some(false),
                    size: Some(5),
                    last_modified_date: Some(EXPECTED_LAST_MODIFIED_THREE.parse().unwrap()),
                    e_tag: Some(EXPECTED_E_TAG_KEY_2.to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
            ]
        );
    }
}
