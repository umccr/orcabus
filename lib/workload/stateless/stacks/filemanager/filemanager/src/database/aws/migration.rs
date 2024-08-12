//! Database migration logic.
//!

use async_trait::async_trait;
use sqlx::migrate;
use sqlx::migrate::Migrator;
use tracing::trace;

use crate::database::{Client, CredentialGenerator, Migrate};
use crate::env::Config;
use crate::error::Error::MigrateError;
use crate::error::Result;

/// A struct to perform database migrations.
#[derive(Debug)]
pub struct Migration {
    client: Client,
}

impl Migration {
    /// Create a new migration.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new migration with a default database client.
    pub async fn with_defaults(
        generator: Option<impl CredentialGenerator>,
        config: &Config,
    ) -> Result<Self> {
        Ok(Self::new(Client::from_generator(generator, config).await?))
    }

    /// Get the underlying sqlx migrator for the migrations.
    pub fn migrator() -> Migrator {
        migrate!("../database/migrations")
    }

    /// Get a reference to the database client.
    pub fn client(&self) -> &Client {
        &self.client
    }
}

#[async_trait]
impl Migrate for Migration {
    async fn migrate(&self) -> Result<()> {
        trace!("applying migrations");
        Self::migrator()
            .run(self.client().pool())
            .await
            .map_err(|err| MigrateError(err.to_string()))
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use lazy_static::lazy_static;
    use sqlx::postgres::PgRow;
    use sqlx::PgPool;
    use sqlx::Row;

    use super::*;

    lazy_static! {
        pub(crate) static ref MIGRATOR: Migrator = Migration::migrator();
    }

    #[sqlx::test(migrations = false)]
    async fn test_migrate(pool: PgPool) {
        let migrate = Migration::new(Client::from_pool(pool));

        let s3_object_exists = check_table_exists(&migrate, "s3_object").await;
        assert!(!s3_object_exists.get::<bool, _>("exists"));

        migrate.migrate().await.unwrap();

        let s3_object_exists = check_table_exists(&migrate, "s3_object").await;
        assert!(s3_object_exists.get::<bool, _>("exists"));
    }

    async fn check_table_exists(migration: &Migration, table_name: &str) -> PgRow {
        sqlx::query(&format!(
            "select exists (select from information_schema.tables where table_name = '{}')",
            table_name
        ))
        .fetch_one(migration.client().pool())
        .await
        .unwrap()
    }
}
