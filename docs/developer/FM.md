# FileManager

```
Namespace: orcabus.fm
```

## How to run FM locally

### Ready Check

```
conda activate orcabus
make up
./lib/workload/stateless/filemanager/scripts/localstack-s3-events-to-sqs.sh # sets up s3 events simulation
cd ./lib/workload/stateless/filemanager && cargo run
```
