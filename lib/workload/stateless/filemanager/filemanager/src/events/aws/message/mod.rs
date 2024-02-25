//! This module controls the serialization and deserialization of different event messages
//! from AWS.

use crate::error::Error;
use crate::error::Result;
use crate::events::aws::message::sqs::SQSEventMessage;
use crate::events::aws::FlatS3EventMessages;
use serde::{Deserialize, Serialize};

pub mod event_bridge;
pub mod sqs;

#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum EventMessage {
    EventBridge(),
    SQS(SQSEventMessage),
}

impl TryFrom<EventMessage> for FlatS3EventMessages {
    type Error = Error;

    fn try_from(message: EventMessage) -> Result<Self> {
        match message {
            EventMessage::EventBridge() => todo!(),
            EventMessage::SQS(message) => message.try_into(),
        }
    }
}
