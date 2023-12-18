use crate::database::{Client, Migrate};
use crate::error::Error::MigrateError;
use crate::error::Result;
use async_trait::async_trait;
use sqlx::migrate;
use sqlx::migrate::Migrator;

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
    pub async fn with_defaults() -> Result<Self> {
        Ok(Self {
            client: Client::default().await?,
        })
    }

    /// Get the underlying sqlx migrator for the migrations.
    pub fn migrator() -> Migrator {
        let mut migrator = migrate!("../database/migrations");
        let aws_migrations = migrate!("../database/migrations/aws");

        migrator
            .migrations
            .to_mut()
            .extend(aws_migrations.migrations.into_owned());

        migrator
    }

    /// Get a reference to the database client.
    pub fn client(&self) -> &Client {
        &self.client
    }
}

#[async_trait]
impl Migrate for Migration {
    async fn migrate(&self) -> Result<()> {
        Self::migrator()
            .run(self.client().pool())
            .await
            .map_err(|err| MigrateError(err.to_string()))
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use sqlx::{PgPool, Row};

    use super::*;

    #[sqlx::test(migrations = false)]
    async fn test_migrate(pool: PgPool) {
        let migrate = Migration::new(Client::new(pool));

        let result = sqlx::query("select * from object")
            .fetch_one(migrate.client.pool())
            .await;

        assert!(result.is_err());

        migrate.migrate().await.unwrap();

        let result = sqlx::query("select * from object")
            .fetch_one(migrate.client.pool())
            .await
            .unwrap();

        assert!(result.is_empty());
    }
}
