use chrono::DateTime;
use core::time::Duration;
use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use dotenvy::var;
use filemanager::database::aws::ingester::Ingester;
use filemanager::database::{Client, Ingest};
use filemanager::events::aws::message::EventType;
use filemanager::events::aws::StorageClass::Standard;
use filemanager::events::aws::{Events, FlatS3EventMessage, FlatS3EventMessages};
use filemanager::events::EventSourceType;
use filemanager::uuid::UuidGenerator;
use itertools::Itertools;
use rand::distributions::{Alphanumeric, DistString};
use rand::rngs::StdRng;
use rand::seq::SliceRandom;
use rand::{Rng, SeedableRng};
use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use std::ops::Add;
use std::time::Instant;
use tokio::runtime::Runtime;

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

    pub fn gen_message(&mut self) -> FlatS3EventMessage {
        const KEY_SIZE: usize = 100;
        const BUCKET_SIZE: usize = 20;
        const VERSION_ID_SIZE: usize = 64;

        FlatS3EventMessage::default()
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
            .with_last_modified_date(DateTime::from_timestamp_millis(self.rng.gen::<u32>() as i64))
            .with_event_time(DateTime::from_timestamp_millis(self.rng.gen::<u32>() as i64))
            .with_event_type(if self.rng.gen_bool(0.5) {
                EventType::Created
            } else {
                EventType::Deleted
            })
    }

    pub fn gen_messages(&mut self, n_same_key: usize) -> FlatS3EventMessages {
        const RATIO_DUPLICATES: f64 = 0.2;
        const RATIO_REORDER: f64 = 0.1;

        let mut messages: Vec<_> = (0..self.n_messages / n_same_key)
            .flat_map(|_| {
                let same_key_messages = vec![self.gen_message(); n_same_key];
                same_key_messages
                    .into_iter()
                    .map(|message| self.fill_non_unique(message))
                    .collect::<Vec<_>>()
            })
            .collect();

        messages.shuffle(&mut self.rng);
        let messages: Vec<_> = messages
            .into_iter()
            .enumerate()
            .map(|(i, message)| message.with_sequencer(Some(i.to_string())))
            .collect();

        let messages: Vec<_> = messages
            .into_iter()
            .flat_map(|message| {
                let message = self.fill_non_unique(message);
                // Create duplicates
                if self.rng.gen_bool(RATIO_DUPLICATES) {
                    vec![
                        message.clone().with_s3_object_id(UuidGenerator::generate()),
                        message,
                    ]
                } else {
                    vec![message]
                }
            })
            .collect();

        let messages = messages
            .into_iter()
            .tuples()
            .flat_map(|(a, b)| {
                // Reorder
                if self.rng.gen_bool(RATIO_REORDER) {
                    vec![b, a]
                } else {
                    vec![a, b]
                }
            })
            .collect();

        FlatS3EventMessages(messages)
    }
}

/// Get a pool connection to a local database.
pub fn database_pool(rt: &Runtime) -> PgPool {
    rt.block_on(
        PgPoolOptions::new()
            .max_connections(200)
            .connect(&var("DATABASE_URL").expect("DATABASE_URL must be set to run benchmarks")),
    )
    .expect("failed to connect to database.")
}

pub fn ingest_bench_elements(
    b: &mut Criterion,
    starts_with: usize,
    n_messages: usize,
    seed: u64,
    runtime: &Runtime,
    pool: &PgPool,
) {
    let mut group = b.benchmark_group("ingest_batch");

    // For each benchmark, the same key represents the number of keys, buckets and version_ids that
    // are the same for a given insert.
    for same_key in [1, 2, 3, 5, 10, 20] {
        let messages = MessageGenerator::new(seed, n_messages).gen_messages(same_key);
        group.throughput(Throughput::Elements(same_key as u64));

        group.bench_with_input(
            BenchmarkId::from_parameter(same_key),
            &messages,
            |b, messages| {
                b.to_async(runtime).iter_custom(|iters| async move {
                    let ingester = Ingester::new(Client::from_ref(pool));

                    let starts_with = EventSourceType::S3(Events::from(
                        MessageGenerator::new(seed, starts_with)
                            .gen_messages(1)
                            .sort_and_dedup(),
                    ));
                    ingester.ingest(starts_with).await.unwrap();

                    let mut total = Duration::default();

                    for _ in 0..iters {
                        // Start measuring after any setup code.
                        let start = Instant::now();
                        for batch in messages.0.chunks(20) {
                            let batch = batch.to_vec();

                            let ingester = Ingester::new(Client::from_ref(pool));

                            let events = EventSourceType::S3(Events::from(
                                FlatS3EventMessages(batch).sort_and_dedup(),
                            ));
                            ingester.ingest(events).await.unwrap();
                        }
                        // Stop before any tear down code.
                        total = total.add(start.elapsed());

                        // Clean-up the database for the next iteration.
                        sqlx::query!("truncate object, s3_object;")
                            .fetch_all(pool)
                            .await
                            .unwrap();
                    }

                    total
                });
            },
        );
    }

    group.finish();
}

/// Benchmark the filemanager ingest function. Note, this focuses on the actual database table
/// structure and query, rather than the event parsing logic.
pub fn ingest_bench(c: &mut Criterion) {
    let runtime = Runtime::new().expect("failed to create tokio runtime");
    let pool = database_pool(&runtime);

    ingest_bench_elements(c, 0, 100, 42, &runtime, &pool);
}

criterion_group!(benches, ingest_bench);
criterion_main!(benches);
