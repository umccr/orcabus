use sqlx::QueryBuilder;
use sqlx::{mysql::MySqlPool, MySql, FromRow};
use crate::error::Result;
use crate::error::Error::DbClientError;

use crate::file::FileAdapter;
use crate::file::Attributes;
use crate::file::File;
use crate::events::EventMessage;

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
    url: String,
}

impl DbClient {
    pub fn new(url: String) -> Self {
        Self {
            url
        }
    }

    pub async fn with_default_client() -> Result<Self> {
        Ok(Self {
            url: std::env::var("DATABASE_URL").map_err(|err| DbClientError(err.to_string()))?
        })
    }

    pub async fn ingest_s3_event(&self, event: EventMessage) -> Result<u64> {
        let pool: sqlx::Pool<sqlx::MySql> = MySqlPool::connect(&self.url).await?;

        let s3 = event.records.iter().map(|record| {
            S3 {
                id: 0,
                bucket: record.s3.bucket.name.clone(),
                key: record.s3.object.key.clone(),
                size: record.s3.object.size,
                e_tag: record.s3.object.e_tag.clone(),
            }
        });


        let mut query_builder: QueryBuilder<MySql> = QueryBuilder::new(
            "INSERT INTO s3(bucket, key, size, e_tag) "
        );
        
        query_builder.push_values(s3, |mut b, s3| {
            b.push_bind(s3.bucket)
                .push_bind(s3.key)
                .push_bind(s3.size)
                .push_bind(s3.e_tag);
        });
        
        let res = query_builder.build().execute(&pool).await?.last_insert_id();

        Ok(res)
    }


    pub async fn s3_query_something(&self, _name: String) -> Result<Vec<S3>> {
        let pool: sqlx::Pool<sqlx::MySql> = MySqlPool::connect(&self.url).await?;

        let key = "foo";
        let objects = sqlx::query_as!(
            S3,
            "
            SELECT id, bucket, `key`, size, e_tag
            FROM s3
            WHERE `key` = ?
            LIMIT 10;
            ",
            key
        )
        .fetch_all(&pool)
        .await?;

        Ok(objects)
    }

    pub async fn plain_query(&self) -> Result<()> {
        let pool = MySqlPool::connect(&self.url).await?;
    
        sqlx::migrate!("./migrations").run(&pool).await?;
    
        let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile LIMIT 10")
            .fetch_one(&pool)
            .await?;
    
        dbg!(&res);
        Ok(())
    }
}

#[derive(Debug, FromRow)]
pub struct S3 {
    pub id: i64,            // TODO: Should this be unsigned for auto (positive) increment?
    pub bucket: String,
    pub key: String,
    pub size: i32,          // TODO: Ditto above, another type than unsigned int for size?
    // pub last_modified_date: NaiveDateTime,
    pub e_tag: String,
}

impl FileAdapter for S3 {
    fn find(&self, _query: Attributes) -> Result<Vec<File>> {
        todo!()
    }
}
