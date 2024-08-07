# Workflow Manager Service

```
Namespace: orcabus.wfm
```

## CDK

See [deploy/README.md](deploy)

## How to run Workflow Manager locally

### Ready Check

- Go to Django project root
```
cd lib/workload/stateless/stacks/workflow-manager
```
_*If you are PyCharm-er and opening the whole `orcabus` project then annotate this level as "source" directory in the project structure dialog._

### Python

- Setup Python environment (conda or venv)
```
conda create -n workflow-manager python=3.12
conda activate workflow-manager
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

#### Generate Workflow Record

```
python manage.py help generate_mock_data
    > Generate mock Workflow data into database for local development and testing
```

```
python manage.py generate_mock_data
```

#### Generate Hello Event

TODO

#### Generate Domain Event

TODO

### Run API

```
python manage.py runserver_plus
```

```
curl -s http://localhost:8000/wfm/v1/workflow | jq
```

```
curl -s http://localhost:8000/wfm/v1/workflow/1 | jq
```

Or visit in browser:
- http://localhost:8000/wfm/v1
- http://localhost:8000/wfm/v1/workflow
- http://localhost:8000/wfm/v1/workflow/1

### API Doc

#### Swagger

- http://localhost:8000/swagger-ui/

#### OpenAPI v3

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
python manage.py test workflow_manager.tests.test_viewsets.WorkflowViewSetTestCase.test_get_api
```

TODO
```
#python manage.py test workflow_manager_proc.tests.test_workflow_event.HelloEventUnitTests.test_sqs_handler
```

```
#python manage.py test workflow_manager_proc.tests.test_workflow_domain.HelloDomainUnitTests.test_marshall
```

```
#python manage.py test workflow_manager_proc.tests.test_workflow_domain.HelloDomainUnitTests.test_unmarshall
```

```
#python manage.py test workflow_manager_proc.tests.test_workflow_domain.HelloDomainUnitTests.test_aws_event_serde
```

```
#python manage.py test workflow_manager_proc.tests.test_workflow_domain.HelloDomainUnitTests.test_put_events_request_entry
```

## Tear Down

```
make down
```



