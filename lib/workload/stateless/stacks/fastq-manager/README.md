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

### DB setup

- Add database config to `../../../../../shared/init-db.sql` for centralised DB setup 
```
CREATE ROLE fastq_manager;
CREATE DATABASE fastq_manager OWNER fastq_manager;
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
python manage.py help generate_mock_fastq_pair
    > Generate mock Fastq data into database for local development and testing
```

```
python manage.py generate_mock_fastq_pair
```


### Run API

```
python manage.py runserver_plus
```

```
curl -s http://localhost:8000/api/v1/fastq | jq
```

```
curl -s http://localhost:8000/api/v1/fastq/1 | jq
```

Or visit in browser:
- http://localhost:8000/api/v1
- http://localhost:8000/api/v1/fastq
- http://localhost:8000/api/v1/fastq/1

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
python manage.py test fastq_manager_proc.tests.test_fastq_pair_proc.FastqPairProcUnitTests.test_handler
```

## Tear Down

```
make down
```



