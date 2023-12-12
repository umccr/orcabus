//! This module provides wrappers around the AWS SDK which allows mocking them for tests.
//!

// Suppress warning when using mock_all
#![allow(dead_code)]

pub mod config;
pub mod s3;
pub mod sqs;
