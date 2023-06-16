# Sequence Run Manager

```
Namespace: orcabus.srm
```

## How to run SRM locally

### Ready Check

- Make sure you have activated conda environment and setup dev toolchain
- At project root, preform:
```
(you may create a dedicated conda env for SRM or use existing one)
conda activate orcabus
make install

(make sure db is up)
make up && make ps
```

### Running

```
cd lib/workload/stateless/sequence_run_manager/src
```

```
python manage.py help
python manage.py showmigrations
python manage.py migrate
```

```
python manage.py help generate_mock_data
    > Generate mock Sequence run data into database for local development and testing
```

```
python manage.py generate_mock_data
```

```
python manage.py runserver_plus
```

```
curl -s http://localhost:8000/sequence | jq
```

```
curl -s http://localhost:8000/sequence/1 | jq
```

Or visit in browser:
- http://localhost:8000
- http://localhost:8000/sequence
- http://localhost:8000/sequence/1

### API Doc

#### Swagger

- http://localhost:8000/swagger
- http://localhost:8000/swagger.json
- http://localhost:8000/swagger.yaml

#### Redoc

- http://localhost:8000/redoc/

#### OpenAPI v3

```
python manage.py generateschema > orcabus.srm.openapi.yaml
```

## Testing

### Run test suite

```
python manage.py test
```

### Unit test

```
python manage.py test sequence_run_manager.tests.test_viewsets.SequenceViewSetTestCase.test_get_api
```
