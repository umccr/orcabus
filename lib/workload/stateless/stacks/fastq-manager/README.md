# FASTQ Manager Service

> FIXME: The following is just an example README as template. You should update it to adapt your service.
---

```
Namespace: orcabus.fqm
```

## CDK

See [deploy/README.md](deploy)

## How to run Fastq Manager locally

### Ready Check

- Go to Django project root
```
cd lib/workload/stateless/stacks/fastq-manager
```
_*If you are PyCharm-er and opening the whole `orcabus` project then annotate this level as "source" directory in the project structure dialog._

### Python

- Setup Python environment (conda or venv)
```
conda create -n fastq-manager python=3.12
conda activate fastq-manager
```

### Make

- At app root, perform
```
make install
make up
make ps
```

### Migration

```
python manage.py help
python manage.py showmigrations
python manage.py migrate
```

### Mock Data

_^^^ please make sure to run `python manage.py migrate` first! ^^^_

#### Generate ReadSet Record

```
python manage.py help generate_mock_data
    > Generate mock Fastq data into database for local development and testing
```

```
python manage.py generate_mock_data
```

#### Generate FASTQ Event

```
python manage.py help generate_mock_fastq_event
    > Generate mock FASTQ SQS event in JSON format for local development and testing
```

```
python manage.py generate_mock_fastq_event | jq
```

#### Generate Domain Event

```
python manage.py help generate_mock_domain_event

    Generate mock FASTQ domain event for local development and testing
    
    options:
      -h, --help            show this help message and exit
      --domain              Deserialized form of FASTQ entity in FASTQRunStateChange
      --envelope            FASTQRunStateChange wrap in AWSEvent envelope
      --boto                AWSEvent to Boto PutEvent API envelope
```

```
python manage.py generate_mock_domain_event | jq
```

```
python manage.py generate_mock_domain_event --domain | jq
```

```
python manage.py generate_mock_domain_event --envelope | jq
```

```
python manage.py generate_mock_domain_event --boto | jq
```

### Run API

```
python manage.py runserver_plus
```

```
curl -s http://localhost:8000/hlo/v1/fastq | jq
```

```
curl -s http://localhost:8000/hlo/v1/fastq/1 | jq
```

Or visit in browser:
- http://localhost:8000/hlo/v1
- http://localhost:8000/hlo/v1/fastq
- http://localhost:8000/hlo/v1/fastq/1

### API Doc

- http://localhost:8000/swagger-ui/
- http://localhost:8000/schema/openapi.json

## Testing

### Coverage report

```
make coverage report
```

_The html report is in `htmlcov/index.html`._

### Run test suite

```
python manage.py test
```

### Unit test

```
python manage.py test fastq_manager.tests.test_viewsets.FastqViewSetTestCase.test_get_api
```

```
python manage.py test fastq_manager_proc.tests.test_fastq_event.FastqEventUnitTests.test_sqs_handler
```

```
python manage.py test fastq_manager_proc.tests.test_fastq_domain.FastqDomainUnitTests.test_marshall
```

```
python manage.py test fastq_manager_proc.tests.test_fastq_domain.FastqDomainUnitTests.test_unmarshall
```

```
python manage.py test fastq_manager_proc.tests.test_fastq_domain.FastqDomainUnitTests.test_aws_event_serde
```

```
python manage.py test fastq_manager_proc.tests.test_fastq_domain.FastqDomainUnitTests.test_put_events_request_entry
```

## Tear Down

```
make down
```



