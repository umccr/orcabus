# Django API Profile

- Use this profile if your microservice need: ORM, API, LAMBDA, SQS

## App

- Consider building a microservice: `hello-manager`

### Ready Check

- Make sure you have activated conda environment and setup dev toolchain
- At project root, preform:

```
conda create -n hello-manager python=3.12
conda activate hello-manager
```

### Bootstrap

```
mkdir -p ./lib/workload/stateless/stacks/hello-manager

pip install Django
django-admin startproject --template skel/django-api hello_manager ./lib/workload/stateless/stacks/hello-manager
```

### Model

```
cd lib/workload/stateless/stacks/hello-manager

(make sure db is up)
make up
make ps
make install

python manage.py inspectdb
python manage.py showmigrations

python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
python manage.py inspectdb
python manage.py inspectdb hello_manager_helloworld
python manage.py test
python manage.py shell_plus

>>> HelloWorld.objects.count()
0

>>> HelloWorld.objects.create(text="Hello World")
<HelloWorld: ID: 1, text: Hello World>

>>> HelloWorld.objects.count()
1

>>> HelloWorld.objects.first()
<HelloWorld: ID: 1, text: Hello World>

>>> exit()
```

### PSQL

```
make psql

orcabus# \l
orcabus# \dt
orcabus# \d hello_manager_helloworld
orcabus# select * from hello_manager_helloworld;
orcabus# \q
```

### REST API

```
python manage.py runserver_plus

(in another terminal)
curl -s http://localhost:8000/hlo/v1/hello | jq
curl -s http://localhost:8000/hlo/v1/hello/1 | jq

open -a "Google Chrome" http://localhost:8000/hlo/v1/
open -a "Google Chrome" http://localhost:8000/swagger-ui/
open -a "Google Chrome" http://localhost:8000/schema/openapi.json

(CRTL+C to stop the server)
```

### Django

```
python manage.py help
```

- See Django doc for more.
- See Django Rest Framework doc for more.

### Test

- Unit test model
```
python manage.py test hello_manager.tests.test_models.HelloModelTests.test_save_hello
```

- Unit test proc handler
```
python manage.py test hello_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
```

- Unit test service layer
```
python manage.py test hello_manager_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
```

### Reset
```
python manage.py reset_db

rm hello_manager/migrations/0001_initial.py

python manage.py showmigrations
```

At this point, you may rename the source code and continue developing the app or simply delete it.

Go back to project root and clean up like so:

```
cd ../../../../../
rm -rf lib/workload/stateless/stacks/hello-manager
conda deactivate
conda env remove -n hello-manager
```

## CDK

Each App stack comes with corresponding `deploy/stack.ts` for CDK boilerplate code as well.
Typically, it is unfinished CDK deployment code. You will need to complete it.
Follow the `FIXME` trail.

This App stack use the following CDK Construct library. You may need to refer their documentation for further enhancement or tweaking.

- https://constructs.dev/packages/@aws-cdk/aws-lambda-python-alpha
