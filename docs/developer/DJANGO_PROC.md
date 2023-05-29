# Django Proc Profile

- Use this profile if your microservice need: ORM, LAMBDA, SQS
- Mainly data processing app and require no API

## App

- Consider building a microservice: `hello_proc_manager`

### Ready Check

- Make sure you have activated conda environment and setup dev toolchain
- At project root, preform:
```
conda activate orcabus
make install
```

### Bootstrap

```
mkdir -p ./lib/workload/stateless/hello_proc_manager

django-admin startproject --template skel/django-proc hello_proc_manager ./lib/workload/stateless/hello_proc_manager

make install
```

### Model

```
cd lib/workload/stateless/hello_proc_manager/src

(make sure db is up)
docker ps

python manage.py inspectdb
python manage.py showmigrations

python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
python manage.py inspectdb
python manage.py inspectdb table hello_proc_manager_helloworld
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
mysql> describe hello_proc_manager_helloworld;
mysql> select * from hello_proc_manager_helloworld;
mysql> \q
```

### Django

```
python manage.py help
```

- Note that not all commands will be possible as this is not web application.
- We are just using Django ORM only as standalone data processing app.
- See Django doc for more about ORM.

### Test

- Unit test model
```
python manage.py test hello_proc_manager.tests.test_models.HelloModelTests.test_save_hello
```

- Unit test proc handler
```
python manage.py test hello_proc_manager_proc.tests.test_hello_proc.HelloProcUnitTests.test_handler
```

- Unit test service layer
```
python manage.py test hello_proc_manager_proc.tests.test_hello_srv.HelloSrvUnitTests.test_get_hello_from_db
```

### Reset
```
python manage.py reset_db

rm hello_proc_manager/migrations/0001_initial.py

python manage.py showmigrations
```

At this point, you may rename source code and, continue developing the app; or simply delete it.

Go back to project root:
```
cd ../../../../../
rm -rf lib/workload/stateless/hello_proc_manager
```

## CDK

Each App stack comes with corresponding `component.ts` for CDK boilerplate code as well.
Typically, it is unfinished CDK deployment code. You will need to complete it.
Follow the `FIXME` trail.

This App stack use the following CDK Construct library. You may need to refer their documentation for further enhancement or tweaking.

- https://constructs.dev/packages/@aws-cdk/aws-lambda-python-alpha
