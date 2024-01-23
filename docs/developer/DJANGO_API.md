# Django API Profile

> !!! TODO NOTE: DJANGO PROJECT DIR STRUCTURE & STEPS NEED TO BE REVISED DUE TO REFACTOR !!! 

- Use this profile if your microservice need: ORM, API, LAMBDA, SQS

## App

- Consider building a microservice: `hello_world_manager`

### Ready Check

- Make sure you have activated conda environment and setup dev toolchain
- At project root, preform:
```
conda activate orcabus
make install
```

### Bootstrap

```
mkdir -p ./lib/workload/stateless/hello_world_manager

django-admin startproject --template skel/django-api hello_world_manager ./lib/workload/stateless/hello_world_manager

make install
```

### Model

```
(make sure db is up)
make up && make ps

cd lib/workload/stateless/hello_world_manager/src

python manage.py inspectdb
python manage.py showmigrations

python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
python manage.py inspectdb
python manage.py inspectdb table hello_world_manager_helloworld
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

### MySQL

```
docker exec -it orcabus_db mysql -h 0.0.0.0 -D orcabus -u root -proot

mysql> show databases;
mysql> show tables;
mysql> describe hello_world_manager_helloworld;
mysql> select * from hello_world_manager_helloworld;
mysql> \q
```

### REST API

```
python manage.py runserver_plus

(in another terminal)
curl -s http://localhost:8000/hello | jq
curl -s http://localhost:8000/hello/1 | jq

open -a Safari http://localhost:8000

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
python manage.py test hello_world_manager.tests.test_models.HelloModelTests.test_save_hello
```

- Unit test proc handler
```
python manage.py test hello_world_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
```

- Unit test service layer
```
python manage.py test hello_world_manager_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
```

### Reset
```
python manage.py reset_db

rm hello_world_manager/migrations/0001_initial.py

python manage.py showmigrations
```

At this point, you may rename the source code and continue developing the app or simply delete it.

Go back to project root:
```
cd ../../../../../
rm -rf lib/workload/stateless/hello_world_manager
```

## CDK

Each App stack comes with corresponding `component.ts` for CDK boilerplate code as well.
Typically, it is unfinished CDK deployment code. You will need to complete it.
Follow the `FIXME` trail.

This App stack use the following CDK Construct library. You may need to refer their documentation for further enhancement or tweaking.

- https://constructs.dev/packages/@aws-cdk/aws-lambda-python-alpha
- https://constructs.dev/packages/@aws-cdk/aws-apigatewayv2-alpha
- https://constructs.dev/packages/@aws-cdk/aws-apigatewayv2-integrations-alpha
- https://constructs.dev/packages/@aws-cdk/aws-apigatewayv2-authorizers-alpha
