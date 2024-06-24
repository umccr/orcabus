//! Query builder involving list operations on the database.
//!

use crate::database::entities::object_group::Entity as ObjectGroupEntity;
use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::Client;
use crate::error::Result;
use sea_orm::EntityTrait;

/// A query builder for list operations.
pub struct ListQueryBuilder<'a> {
    client: &'a Client,
}

impl<'a> ListQueryBuilder<'a> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self { client }
    }

    /// Find all object groups.
    pub async fn list_object_groups(&self) -> Result<Vec<ObjectGroup>> {
        Ok(ObjectGroupEntity::find()
            .all(self.client.connection_ref())
            .await?)
    }
}
