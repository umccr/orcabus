//! Logic for creating uuids.
//!

use uuid::Uuid;

/// A wrapper around the Uuid crate for defining the way uuids are generated
/// in the filemanager.
#[derive(Debug, Default)]
pub struct UuidGenerator;

impl UuidGenerator {
    /// Generate a new uuid.
    pub fn generate() -> Uuid {
        Uuid::now_v7()
    }

    /// Generate n uuids into a vector.
    pub fn generate_n(n: usize) -> Vec<Uuid> {
        (0..n).map(|_| Self::generate()).collect()
    }
}

#[cfg(test)]
mod tests {
    use itertools::Itertools;

    use super::*;

    #[test]
    fn generate_n() {
        let uuids = UuidGenerator::generate_n(1000);
        let unique: Vec<Uuid> = uuids.clone().into_iter().unique().collect();

        assert_eq!(uuids.len(), 1000);
        assert_eq!(uuids, unique);
    }
}
