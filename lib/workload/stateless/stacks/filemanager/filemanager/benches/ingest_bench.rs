use chrono::DateTime;
use criterion::{criterion_group, criterion_main, Criterion, Throughput, BenchmarkId};
use dotenvy::var;
use filemanager::events::aws::message::EventType;
use filemanager::events::aws::StorageClass::Standard;
use filemanager::events::aws::{Events, FlatS3EventMessage, FlatS3EventMessages};
use filemanager::uuid::UuidGenerator;
use itertools::Itertools;
use rand::distributions::{Alphanumeric, DistString};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use tokio::runtime::Runtime;
use filemanager::database::aws::ingester::Ingester;
use filemanager::database::{Client, Ingest};
use filemanager::events::EventSourceType;

pub struct MessageGenerator {
    rng: StdRng,
    n_messages: usize,
}

impl MessageGenerator {
    pub fn new(seed: u64, n_messages: usize) -> Self {
        Self {
            rng: StdRng::seed_from_u64(seed),
            n_messages,
        }
    }

    pub fn gen_message(&mut self, sequencer: String) -> FlatS3EventMessage {
        const KEY_SIZE: usize = 100;
        const BUCKET_SIZE: usize = 20;
        const VERSION_ID_SIZE: usize = 64;

        FlatS3EventMessage::default()
            .with_sequencer(Some(sequencer))
            .with_bucket(Alphanumeric.sample_string(&mut self.rng, BUCKET_SIZE))
            .with_key(Alphanumeric.sample_string(&mut self.rng, KEY_SIZE))
            .with_version_id(Alphanumeric.sample_string(&mut self.rng, VERSION_ID_SIZE))
    }

    pub fn fill_non_unique(&mut self, message: FlatS3EventMessage) -> FlatS3EventMessage {
        const E_TAG_SIZE: usize = 32;

        message
            .with_s3_object_id(UuidGenerator::generate())
            .with_size(Some(self.rng.gen::<u32>() as i64))
            .with_e_tag(Some(Alphanumeric.sample_string(&mut self.rng, E_TAG_SIZE)))
            .with_storage_class(Some(Standard))
            .with_last_modified_date(DateTime::from_timestamp_millis(self.rng.gen()))
            .with_event_time(DateTime::from_timestamp_millis(self.rng.gen()))
            .with_event_type(if self.rng.gen_bool(0.5) {
                EventType::Created
            } else {
                EventType::Deleted
            })
    }

    pub fn gen_messages(&mut self) -> FlatS3EventMessages {
        const RATIO_DUPLICATES: f64 = 0.2;
        const RATIO_REORDER: f64 = 0.1;

        const N_UNIQUE: usize = 10;
        const N_TEN_KEYS_SAME: usize = 10;
        const CHARSET: &str = "abcdefghijklmnopqrstuvwxyz";

        let messages: Vec<FlatS3EventMessage> = (0..self.n_messages / (N_UNIQUE + N_TEN_KEYS_SAME)).flat_map(|i| {
            // Create messages where some of the bucket, key and version_id combinations are unique, and
            // where some of the combinations has the same bucket, key and version_id.
            let mut gen = |sequencer: String| self.gen_message(sequencer.to_string());

            let one: Vec<_> = (0..N_UNIQUE)
                .map(|j| gen(i.to_string() + &CHARSET.chars().nth(j).unwrap().to_string()))
                .collect();

            let ten = vec![gen(i.to_string()); N_TEN_KEYS_SAME];
            let ten = ten
                .into_iter()
                .enumerate()
                .map(|(j, message)| {
                    message.with_sequencer(Some(i.to_string() + &CHARSET.chars().nth(j + N_UNIQUE).unwrap().to_string()))
                })
                .collect();

            [one, ten].concat()
        }).collect();

        let messages: Vec<FlatS3EventMessage> = messages.into_iter().flat_map(|message| {
            let message = self.fill_non_unique(message);
            // Create duplicates
            if self.rng.gen_bool(RATIO_DUPLICATES) {
                vec![message.clone().with_s3_object_id(UuidGenerator::generate()), message]
            } else {
               vec![message]
            }
        }).collect();

        let messages = messages.into_iter().tuples().flat_map(|(a, b)| {
            // Reorder
            if self.rng.gen_bool(RATIO_REORDER) {
                vec![b, a]
            } else {
                vec![a, b]
            }
        }).collect();

        FlatS3EventMessages(messages)
    }
}

/// Get a pool connection to a local database.
pub fn database_pool(rt: &Runtime) -> PgPool {
    rt
        .block_on(
            PgPoolOptions::new()
                .max_connections(200)
                .connect(&var("DATABASE_URL").expect("DATABASE_URL must be set to run benchmarks")),
        )
        .expect("failed to connect to database.")
}

/// Benchmark the filemanager ingest function. Note, this focuses on the actual database table
/// structure and query, rather than the event parsing logic.
pub fn ingest_bench(c: &mut Criterion) {
    let runtime = Runtime::new().expect("failed to create tokio runtime");
    let messages = MessageGenerator::new(42, 100000).gen_messages();

    let pool = database_pool(&runtime);
    let ingester = Ingester::new(Client::new(pool));
    
    let mut group = c.benchmark_group("ingest_batch");
    group.throughput(Throughput::Elements(20));
    
    for (i, batch) in messages.0.into_iter().chunks(20).into_iter().enumerate() {
        let batch: Vec<FlatS3EventMessage> = batch.collect();
        
        group.bench_with_input(BenchmarkId::from_parameter(i), &batch, |b, batch| {
            b.to_async(&runtime).iter(|| async {
                let events = EventSourceType::S3(Events::from(FlatS3EventMessages(batch.clone()).sort_and_dedup()));
                ingester.ingest(events).await.unwrap();
            });
        });
    }
    
    group.finish();
}

criterion_group!(benches, ingest_bench);
criterion_main!(benches);
