use crate::database::Client;
use crate::error::Error::MigrateError;
use crate::error::Result;
use sqlx::migrate;

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

    /// Apply migrations.
    pub async fn migrate(&mut self) -> Result<()> {
        // Note, these get compiled into the source code.
        migrate!("../database/migrations")
            .run(self.client().pool())
            .await
            .map_err(|err| MigrateError(err.to_string()))?;
        migrate!("../database/migrations/aws")
            .run(self.client().pool())
            .await
            .map_err(|err| MigrateError(err.to_string()))
    }

    /// Get a reference to the database client.
    pub fn client(&self) -> &Client {
        &self.client
    }
}
