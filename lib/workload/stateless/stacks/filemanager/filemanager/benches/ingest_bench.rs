use chrono::DateTime;
use core::time::Duration;
use criterion::{
    criterion_group, criterion_main, BenchmarkGroup, BenchmarkId, Criterion, Throughput,
};
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

/// A message generator generates test S3 messages for filemanager.
#[derive(Debug)]
pub struct MessageGenerator {
    rng: StdRng,
    n_messages: usize,
}

impl MessageGenerator {
    /// Create a new message generator.
    pub fn new(seed: u64, n_messages: usize) -> Self {
        Self {
            rng: StdRng::seed_from_u64(seed),
            n_messages,
        }
    }

    /// Generate a message using constant key, bucket and version_id sizes.
    pub fn gen_message(&mut self) -> FlatS3EventMessage {
        const KEY_SIZE: usize = 100;
        const BUCKET_SIZE: usize = 20;
        const VERSION_ID_SIZE: usize = 64;

        FlatS3EventMessage::default()
            .with_bucket(Alphanumeric.sample_string(&mut self.rng, BUCKET_SIZE))
            .with_key(Alphanumeric.sample_string(&mut self.rng, KEY_SIZE))
            .with_version_id(Alphanumeric.sample_string(&mut self.rng, VERSION_ID_SIZE))
    }

    /// Fill the message with different values that doesn't affect the unique constraint of the
    /// database.
    pub fn fill_non_unique(&mut self, message: FlatS3EventMessage) -> FlatS3EventMessage {
        const E_TAG_SIZE: usize = 32;

        message
            .with_s3_object_id(UuidGenerator::generate())
            .with_object_id(UuidGenerator::generate())
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

    /// Generate messages with some proportion of them duplicated, and reordered. Sequencers are
    /// always increasing.
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
                // Create duplicates
                if self.rng.gen_bool(RATIO_DUPLICATES) {
                    vec![
                        message
                            .clone()
                            .with_s3_object_id(UuidGenerator::generate())
                            .with_object_id(UuidGenerator::generate()),
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

pub const RAND_SEED: u64 = 42;

/// Benchmark the filemanager ingest function. Note, this focuses on the actual database table
/// structure and query, rather than the event parsing logic.
///
/// This benchmark shows how the execution time of inserts changes across when the number of
/// events with the same key, bucket and version_id are inserted. This hits the v1 original insert
/// condition which searches for all matching objects with the same key, bucket and version_id
/// before inserting.
///
/// This function can be configured to run with an initial database that has `start_with` number of
/// records in it.
pub fn ingest_bench_elements(
    c: &mut Criterion,
    n_messages: usize,
    runtime: &Runtime,
    pool: &PgPool,
    measurement_time_secs: u64,
    sample_size: usize,
) {
    let mut group = c.benchmark_group("ingest");
    group.measurement_time(Duration::from_secs(measurement_time_secs));
    group.sample_size(sample_size);

    let bench = |group: &mut BenchmarkGroup<_>, same_key: usize, function_name: &str| {
        group.bench_with_input(
            BenchmarkId::new(function_name, same_key),
            &same_key,
            |b, same_key| {
                b.to_async(runtime).iter_custom(|iters| async move {
                    let messages =
                        MessageGenerator::new(RAND_SEED, n_messages).gen_messages(*same_key);

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

                            if function_name.contains("v2") {
                                ingester.ingest_events_v2(events).await.unwrap();
                            } else {
                                ingester.ingest(events).await.unwrap();
                            }
                        }
                        // Stop before any tear down code.
                        total = total.add(start.elapsed());

                        for message in messages.0.iter() {
                            // Clean-up the database for the next iteration.
                            sqlx::query!(
                                "delete from s3_object where s3_object_id = $1",
                                message.s3_object_id
                            )
                            .fetch_all(pool)
                            .await
                            .unwrap();
                            sqlx::query!(
                                "delete from object where object_id = $1",
                                message.object_id
                            )
                            .fetch_all(pool)
                            .await
                            .unwrap();
                            sqlx::query!(
                                "delete from s3_object_v2 where s3_object_id = $1",
                                message.s3_object_id
                            )
                            .fetch_all(pool)
                            .await
                            .unwrap();
                            sqlx::query!(
                                "delete from object_v2 where object_id = $1",
                                message.object_id
                            )
                            .fetch_all(pool)
                            .await
                            .unwrap();
                        }
                    }

                    total
                });
            },
        );
    };

    for starts_with in [0, 100000] {
        let ingester = Ingester::new(Client::from_ref(pool));

        let start = Instant::now();
        println!("starting initial record ingestion process");

        let starts_with_messages = EventSourceType::S3(Events::from(
            MessageGenerator::new(RAND_SEED, starts_with)
                .gen_messages(1)
                .sort_and_dedup(),
        ));
        println!(
            "{} events created, took {} seconds",
            starts_with,
            start.elapsed().as_secs()
        );

        // Clean up any previous iterations.
        runtime.block_on(async {
            sqlx::query!("truncate table s3_object, object, s3_object_v2, object_v2")
                .fetch_all(pool)
                .await
                .unwrap();
        });

        runtime.block_on(async {
            ingester.ingest(starts_with_messages.clone()).await.unwrap();
        });
        println!(
            "{} events ingested v1, took {} seconds",
            starts_with,
            start.elapsed().as_secs()
        );

        runtime.block_on(async {
            ingester
                .ingest_events_v2(starts_with_messages)
                .await
                .unwrap();
        });
        println!(
            "{} events ingested v2, took {} seconds",
            starts_with,
            start.elapsed().as_secs()
        );

        // For each benchmark, the same key represents the number of keys, buckets and version_ids that
        // are the same for a given insert.
        for same_key in [1, 2, 3, 5, 10, 20, 50, 100] {
            group.throughput(Throughput::Elements(same_key as u64));

            bench(
                &mut group,
                same_key,
                &format!("v1_starts_with_{}", starts_with),
            );
            bench(
                &mut group,
                same_key,
                &format!("v2_starts_with_{}", starts_with),
            );
        }
    }

    group.finish();
}

/// Benchmark the filemanager ingest function starting with an empty database, and a small database
/// with 100000 records.
pub fn ingest_bench_database(c: &mut Criterion) {
    let runtime = Runtime::new().expect("failed to create tokio runtime");
    let pool = database_pool(&runtime);

    ingest_bench_elements(c, 1000, &runtime, &pool, 300, 50);
}

criterion_group!(benches, ingest_bench_database);
criterion_main!(benches);
