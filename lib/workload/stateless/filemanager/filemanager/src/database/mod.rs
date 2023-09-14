pub mod s3;

use crate::error::Error::DbClientError;
use crate::error::Result;
use aws_sdk_s3::types::StorageClass;
use chrono::{DateTime, NaiveDateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use sqlx::FromRow;
use utoipa::{IntoParams, ToSchema};

use crate::file::Attributes;
use crate::file::File;
use crate::file::FileAdapter;
//
// /// This matches the database object schema. Missing fields will be filled in/calculated.
// #[derive(Debug, ToSchema, IntoParams, Clone)]
// pub struct Object {
//     pub bucket: String,
//     pub key: String,
//     pub size: u64,
//     pub e_tag: String,
//     pub last_modified_date: Option<DateTime<Utc>>,
//     pub portal_run_id: String,
//     pub cloud_object: Option<CloudObject>,
// }

// #[derive(Debug, Clone)]
// pub enum CloudObject {
//     S3(aws::CloudObject),
// }

// #[derive(Debug, FromRow)]
// struct GDS {
//     id: u64,
//     path: String,
//     // name: String,
//     // volume_id: u64,
//     // volume_name: String,
//     // size: u64
//     // time_created: chrono::DateTime<chrono::Utc>,
//     // time_archived: chrono::DateTime<chrono::Utc>,
// }

#[derive(Debug)]
pub struct DbClient {
    pool: PgPool,
}

impl DbClient {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn new_with_defaults() -> Result<Self> {
        let url = std::env::var("DATABASE_URL").map_err(|err| DbClientError(err.to_string()))?;

        Ok(Self {
            pool: PgPool::connect(&url).await?
        })
    }

    // pub async fn ingest_s3_event(&self, event: S3EventMessage) -> Result<u64> {
    //     let pool: sqlx::Pool<sqlx::MySql> = MySqlPool::connect(&self.url).await?;
    //
    //     let s3 = event.records.iter().map(|record| S3 {
    //         id: 0,
    //         bucket: record.s3.bucket.name.clone(),
    //         key: record.s3.object.key.clone(),
    //         size: record.s3.object.size,
    //         e_tag: record.s3.object.e_tag.clone(),
    //         last_modified_date: record.head.clone().map(Self::get_datetime).flatten(),
    //         // owner: record.head.map(|head| head.metadata().)
    //         storage_class: record
    //             .head
    //             .clone()
    //             .map(|head| head.storage_class().cloned())
    //             .flatten(),
    //     });
    //
    //     let mut query_builder: QueryBuilder<MySql> = QueryBuilder::new(
    //         "INSERT INTO aws(bucket, `key`, size, e_tag, last_modified_date, storage_class) ",
    //     );
    //
    //     query_builder.push_values(s3, |mut b, s3| {
    //         b.push_bind(s3.bucket)
    //             .push_bind(s3.key)
    //             .push_bind(s3.size)
    //             .push_bind(s3.e_tag)
    //             .push_bind(s3.last_modified_date)
    //             .push_bind(
    //                 s3.storage_class
    //                     .map(|storage_class| storage_class.as_str().to_string()),
    //             );
    //     });
    //
    //     let res = query_builder.build().execute(&pool).await?.last_insert_id();
    //
    //     Ok(res)
    // }

    // pub async fn s3_query_something(&self, _name: String) -> Result<Vec<S3>> {
    //     let pool: sqlx::Pool<sqlx::MySql> = MySqlPool::connect(&self.url).await?;
    //
    //     let key = "foo";
    //     // let objects = sqlx::query_as!(
    //     //     S3,
    //     //     "
    //     //     SELECT id, bucket, `key`, size, e_tag, last_modified_date, storage_class
    //     //     FROM aws
    //     //     WHERE `key` = ?
    //     //     LIMIT 10;
    //     //     ",
    //     //     key
    //     // )
    //     // .fetch_all(&pool)
    //     // .await?;
    //
    //     // Ok(objects)
    //     Ok(vec![])
    // }

    // pub async fn plain_query(&self) -> Result<()> {
    //     let pool = MySqlPool::connect(&self.url).await?;
    //
    //     sqlx::migrate!("./migrations").run(&pool).await?;
    //
    //     let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile LIMIT 10")
    //         .fetch_one(&pool)
    //         .await?;
    //
    //     dbg!(&res);
    //     Ok(())
    // }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }
}

#[derive(Debug, FromRow)]
pub struct S3 {
    pub id: i64, // TODO: Should this be unsigned for auto (positive) increment?
    pub bucket: String,
    pub key: String,
    pub size: i32, // TODO: Ditto above, another type than unsigned int for size?
    pub e_tag: String,
    pub last_modified_date: Option<DateTime<Utc>>,
    // pub owner: Option<String>,
    pub storage_class: Option<StorageClass>,
}

impl FileAdapter for S3 {
    fn find(&self, _query: Attributes) -> Result<Vec<File>> {
        todo!()
    }
}
