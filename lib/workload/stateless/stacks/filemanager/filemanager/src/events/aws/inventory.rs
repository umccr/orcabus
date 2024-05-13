//! Handles S3 Inventory reports and converts them to events that can be ingested.
//!

use std::io::{BufReader, Cursor, Read};
use std::result;

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
use mockall_double::double;
use orc_rust::error::OrcError;
use orc_rust::ArrowReaderBuilder;
use parquet::arrow::ParquetRecordBatchStreamBuilder;
use parquet::errors::ParquetError;
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::from_slice;
use serde_with::{serde_as, DisplayFromStr};

#[double]
use crate::clients::aws::s3::Client;
use crate::error::Error::S3InventoryError;
use crate::error::{Error, Result};
use crate::events::aws::message::EventType::Created;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::uuid::UuidGenerator;

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
    pub async fn parse_csv(&self, schema: &str, body: &[u8]) -> Result<Vec<Record>> {
        let mut inventory_bytes = vec![];
        MultiGzDecoder::new(BufReader::new(body))
            .read_to_end(&mut inventory_bytes)
            .map_err(|err| S3InventoryError(format!("decompressing CSV: {}", err)))?;

        // AWS seems to return extra newlines at the end of the CSV, so we remove these
        let inventory_bytes = Self::trim_whitespace(inventory_bytes.as_slice());

        let mut header_record = StringRecord::new();
        ReaderBuilder::new()
            .trim(Trim::All)
            .has_headers(false)
            .from_reader(schema.as_bytes())
            .read_record(&mut header_record)?;

        let mut csv = ReaderBuilder::new()
            .trim(Trim::All)
            .from_reader(inventory_bytes);
        csv.set_headers(header_record);

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
        from_slice::<Vec<Record>>(buf.as_slice()).map_err(|err| {
            S3InventoryError(format!("failed to deserialize json from arrow: {}", err))
        })
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
            .get_object(key.as_ref(), bucket.as_ref())
            .await
            .map_err(|err| S3InventoryError(err.to_string()))?
            .body
            .collect()
            .await
            .map_err(|err| S3InventoryError(err.to_string()))?
            .to_vec())
    }

    /// Verify the md5sum of the data returning an error if there is a mismatch.
    fn verify_md5<T: AsRef<[u8]>>(data: T, verify_with: T) -> Result<()> {
        if md5::compute(data).0
            != hex::decode(&verify_with)
                .map_err(|err| S3InventoryError(format!("decoding hex string: {}", err)))?
                .as_slice()
        {
            return Err(S3InventoryError(
                "mismatched MD5 checksums in inventory manifest".to_string(),
            ));
        }

        Ok(())
    }

    /// Parse byte data into a manifest.json and then into records.
    async fn json_manifest_from_bytes(&self, bytes: &[u8]) -> Result<Vec<Record>> {
        self.parse_manifest(from_slice(bytes)?).await
    }

    /// Parse records from a bucket and key containing an S3 inventory manifest file.
    pub async fn parse_manifest_key<K: AsRef<str>>(
        &self,
        key: K,
        bucket: K,
    ) -> Result<Vec<Record>> {
        if key.as_ref().ends_with(".json") {
            self.parse_manifest_json(key, bucket).await
        } else {
            self.parse_manifest_checksum(key, bucket).await
        }
    }

    /// Parse records from a bucket and key containing an S3 inventory manifest.checksum. This assumes
    /// the corresponding manifest.json has the same key and bucket except with .json as the suffix.
    pub async fn parse_manifest_checksum<K: AsRef<str>>(
        &self,
        key: K,
        bucket: K,
    ) -> Result<Vec<Record>> {
        let checksum = self.get_object_bytes(key.as_ref(), bucket.as_ref()).await?;

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
        Self::verify_md5(
            manifest.as_slice(),
            Self::trim_whitespace(checksum.as_slice()),
        )?;

        self.json_manifest_from_bytes(manifest.as_slice()).await
    }

    /// Parse records from a bucket and key containing an S3 inventory manifest.json.
    pub async fn parse_manifest_json<K: AsRef<str>>(
        &self,
        key: K,
        bucket: K,
    ) -> Result<Vec<Record>> {
        let data = self.get_object_bytes(key, bucket).await?;

        self.json_manifest_from_bytes(data.as_slice()).await
    }

    /// Parse a manifest into records.
    pub async fn parse_manifest(&self, manifest: Manifest) -> Result<Vec<Record>> {
        let arn: ResourceName = manifest
            .destination_bucket
            .parse()
            .map_err(|err| S3InventoryError(format!("parsing destination bucket arn: {}", err)))?;

        if arn.service != Service::S3.into() {
            return Err(S3InventoryError(
                "destination bucket ARN is not S3".to_string(),
            ));
        }

        let bucket = arn.resource.to_string();

        // TODO: consider streaming a file and reading records without placing them into memory first.
        let inventories = join_all(manifest.files.iter().map(|file| async {
            let inventory = self
                .client
                .get_object(&file.key, &bucket)
                .await
                .map_err(|err| S3InventoryError(format!("getting inventory: {}", err)))?;
            let body = inventory
                .body
                .collect()
                .await
                .map_err(|_| S3InventoryError("collecting inventory bytes".to_string()))?
                .to_vec();

            Self::verify_md5(body.as_slice(), file.md5_checksum.as_bytes())?;

            match manifest.file_format {
                InventoryFormat::Csv => {
                    self.parse_csv(&manifest.file_schema, body.as_slice()).await
                }
                InventoryFormat::Parquet => self.parse_parquet(body).await,
                InventoryFormat::Orc => self.parse_orc(body).await,
                _ => Err(S3InventoryError(
                    "unsupported manifest file type".to_string(),
                )),
            }
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
        S3InventoryError(error.to_string())
    }
}

impl From<ParquetError> for Error {
    fn from(error: ParquetError) -> Self {
        S3InventoryError(error.to_string())
    }
}

impl From<ArrowError> for Error {
    fn from(error: ArrowError) -> Self {
        S3InventoryError(error.to_string())
    }
}

impl From<OrcError> for Error {
    fn from(error: OrcError) -> Self {
        S3InventoryError(error.to_string())
    }
}

/// An S3 inventory record.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Record {
    #[serde(alias = "Bucket")]
    bucket: String,
    #[serde(alias = "Key")]
    key: String,
    #[serde(alias = "VersionId")]
    version_id: Option<String>,
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
    file_schema: String,
    files: Vec<File>,
}

/// The files inside the manifest.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct File {
    key: String,
    #[serde(rename = "MD5checksum")]
    md5_checksum: String,
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
            e_tag,
            // Set this to the empty string so that any deleted events after this can bind to this
            // created event, as they are always greater than this event.
            sequencer: Some("".to_string()),
            version_id: version_id.unwrap_or_else(FlatS3EventMessage::default_version_id),
            storage_class,
            last_modified_date,
            sha256: None,
            // Anything in an inventory report is always a created event.
            event_type: Created,
            number_reordered: 0,
            number_duplicate_events: 0,
        }
    }
}

#[cfg(test)]
mod tests {
    use aws_sdk_s3::operation::get_object::GetObjectOutput;
    use aws_sdk_s3::primitives::ByteStream;
    use flate2::read::GzEncoder;
    use mockall::predicate::eq;
    use serde_json::json;
    use serde_json::Value;

    use crate::events::aws::inventory::Manifest;

    use super::*;

    const ORC_MANIFEST_SCHEMA: &str = "struct<bucket:string,key:string,version_id:string,\
        is_latest:boolean,is_delete_marker:boolean,size:bigint,last_modified_date:timestamp,\
        e_tag:string,storage_class:string,is_multipart_uploaded:boolean,replication_status:string,\
        encryption_status:string,object_lock_retain_until_date:timestamp,object_lock_mode:string,\
        object_lock_legal_hold_status:string,intelligent_tiering_access_tier:string,\
        bucket_key_status:string,checksum_algorithm:string,\
        object_access_control_list:string,object_owner:string>";

    const PARQUET_MANIFEST_SCHEMA: &str =
        "message s3.inventory {  required binary bucket (STRING);  \
        required binary key (STRING);  optional binary version_id (STRING);  \
        optional boolean is_latest;  optional boolean is_delete_marker;  \
        optional int64 size;  optional int64 last_modified_date (TIMESTAMP(MILLIS,true));  \
        optional binary e_tag (STRING);  optional binary storage_class (STRING);  \
        optional boolean is_multipart_uploaded;  optional binary replication_status (STRING);  \
        optional binary encryption_status (STRING);  \
        optional int64 object_lock_retain_until_date (TIMESTAMP(MILLIS,true));  \
        optional binary object_lock_mode (STRING);  \
        optional binary object_lock_legal_hold_status (STRING);  \
        optional binary intelligent_tiering_access_tier (STRING);  \
        optional binary bucket_key_status (STRING);  optional binary checksum_algorithm (STRING);  \
        optional binary object_access_control_list (STRING);  \
        optional binary object_owner (STRING);}";

    const CSV_MANIFEST_SCHEMA: &str = "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner";

    const MANIFEST_KEY: &str = "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce";
    const MANIFEST_BUCKET: &str = "example-inventory-destination-bucket";
    const EXPECTED_CHECKSUM: &str = "f11166069f1990abeb9c97ace9cdfabc"; // pragma: allowlist secret

    #[tokio::test]
    async fn parse_csv_manifest_from_checksum() {
        let (mut client, checksum) = test_csv_manifest();

        let bytes = serde_json::to_vec_pretty(&expected_csv_manifest(checksum)).unwrap();
        let checksum = format!("{}\n", hex::encode(md5::compute(bytes.as_slice()).0))
            .as_bytes()
            .to_vec();
        set_client_manifest_expectations(&mut client, bytes);

        client
            .expect_get_object()
            .with(eq("manifest.checksum"), eq(MANIFEST_BUCKET))
            .once()
            .returning(move |_, _| {
                Ok(GetObjectOutput::builder()
                    .body(ByteStream::from(checksum.clone()))
                    .build())
            });

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest_key("manifest.checksum", MANIFEST_BUCKET)
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[tokio::test]
    async fn parse_csv_manifest_from_key() {
        let (mut client, checksum) = test_csv_manifest();

        let bytes = serde_json::to_vec_pretty(&expected_csv_manifest(checksum)).unwrap();
        set_client_manifest_expectations(&mut client, bytes);

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest_key("manifest.json", MANIFEST_BUCKET)
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[tokio::test]
    async fn parse_csv_manifest() {
        let (client, checksum) = test_csv_manifest();

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest(expected_csv_manifest(checksum))
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
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
        let mut client = Client::default();
        set_client_expectations(&InventoryFormat::Csv, &mut client, bytes);

        let inventory = Inventory::new(client);
        let result = inventory
            .parse_manifest(expected_manifest(
                "Size, Bucket, Key, VersionId, IsLatest, IsDeleteMarker, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner"
                    .to_string(),
                InventoryFormat::Csv,
                checksum,
            ))
            .await
            .unwrap();

        assert_csv_records(result.as_slice());
    }

    #[test]
    fn deserialize_csv_manifest() {
        let manifest = expected_json_manifest(&InventoryFormat::Csv);

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(result, expected_csv_manifest(EXPECTED_CHECKSUM.to_string()));
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

    fn set_client_manifest_expectations(s3_client: &mut Client, data: Vec<u8>) {
        s3_client
            .expect_get_object()
            .with(eq("manifest.json"), eq(MANIFEST_BUCKET))
            .once()
            .returning(move |_, _| {
                Ok(GetObjectOutput::builder()
                    .body(ByteStream::from(data.clone()))
                    .build())
            });
    }

    fn test_csv_manifest() -> (Client, String) {
        let data = concat!(
            r#""bucket","inventory_test/","","true","false","0","2024-04-22T01:11:06.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key1","","true","false","0","2024-04-22T01:13:28.000Z","d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n",
            r#""bucket","inventory_test/key2","","true","false","5","2024-04-22T01:14:53.000Z","d8e8fca2dc0f896fd7cb4cb0031ba249","STANDARD","false","","SSE-S3","","","","","DISABLED","","e30K","""#, // pragma: allowlist secret
            "\n\n"
        );

        let mut bytes = vec![];
        let mut reader = GzEncoder::new(data.as_bytes(), Default::default());
        reader.read_to_end(&mut bytes).unwrap();

        let checksum = hex::encode(md5::compute(bytes.as_slice()).0);
        let mut client = Client::default();
        set_client_expectations(&InventoryFormat::Csv, &mut client, bytes);

        (client, checksum)
    }

    fn set_client_expectations(
        file_format: &InventoryFormat,
        s3_client: &mut Client,
        data: Vec<u8>,
    ) {
        let ending = ending_from_format(file_format);

        s3_client
            .expect_get_object()
            .with(
                eq(format!("{}{}", MANIFEST_KEY, ending)),
                eq(MANIFEST_BUCKET),
            )
            .once()
            .returning(move |_, _| {
                Ok(GetObjectOutput::builder()
                    .body(ByteStream::from(data.clone()))
                    .build())
            });
    }

    fn expected_json_manifest(format: &InventoryFormat) -> Value {
        let schema = match format {
            InventoryFormat::Csv => CSV_MANIFEST_SCHEMA,
            InventoryFormat::Orc => ORC_MANIFEST_SCHEMA,
            InventoryFormat::Parquet => PARQUET_MANIFEST_SCHEMA,
            _ => "",
        };

        // Taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest
        json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": format!("arn:aws:s3:::{}", MANIFEST_BUCKET),
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": format.as_str(),
            "fileSchema": schema,
            "files": [{
                "key": format!("{}{}", MANIFEST_KEY, ending_from_format(format)),
                "size": 2147483647,
                "MD5checksum": EXPECTED_CHECKSUM
            }]
        })
    }

    fn expected_manifest(
        file_schema: String,
        file_format: InventoryFormat,
        md5_checksum: String,
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
        expected_manifest(
            ORC_MANIFEST_SCHEMA.to_string(),
            InventoryFormat::Orc,
            checksum,
        )
    }

    fn expected_parquet_manifest(checksum: String) -> Manifest {
        expected_manifest(
            PARQUET_MANIFEST_SCHEMA.to_string(),
            InventoryFormat::Parquet,
            checksum,
        )
    }

    fn expected_csv_manifest(checksum: String) -> Manifest {
        expected_manifest(
            CSV_MANIFEST_SCHEMA.to_string(),
            InventoryFormat::Csv,
            checksum,
        )
    }

    fn assert_csv_records(result: &[Record]) {
        assert_eq!(
            result,
            vec![
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/".to_string(),
                    version_id: None,
                    size: Some(0),
                    last_modified_date: Some("2024-04-22T01:11:06.000Z".parse().unwrap()),
                    e_tag: Some("d41d8cd98f00b204e9800998ecf8427e".to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/key1".to_string(),
                    version_id: None,
                    size: Some(0),
                    last_modified_date: Some("2024-04-22T01:13:28.000Z".parse().unwrap()),
                    e_tag: Some("d41d8cd98f00b204e9800998ecf8427e".to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
                Record {
                    bucket: "bucket".to_string(),
                    key: "inventory_test/key2".to_string(),
                    version_id: None,
                    size: Some(5),
                    last_modified_date: Some("2024-04-22T01:14:53.000Z".parse().unwrap()),
                    e_tag: Some("d8e8fca2dc0f896fd7cb4cb0031ba249".to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
            ]
        );
    }
}
