# Token Service

This service provides the JWT token for API authentication and authorization (AAI) purpose. We use the Cognito as AAI service broker and, it is set up at our infrastructure repo. This service maintains 2 secrets with rotation enabled.

## JWT

For most cases, you would want to lookup JWT token from the secret manager at the following coordinate.
```
orcabus/token-service-jwt
```

An example Python boto3 snippet code as follows.

```python
import json
import boto3

sm_client = boto3.client('secretsmanager')

resp = sm_client().get_secret_value(SecretId='orcabus/token-service-jwt')

jwt_json = resp['SecretString']
jwt_dict = json.loads(jwt_json)

print(jwt_dict['id_token'])  # this is your JWT token to use for calling API endpoint
```

Alternatively, try [libumccr/aws/libsm](https://github.com/umccr/libumccr/blob/main/libumccr/aws/libsm.py) module, like so.

```python
import json
from libumccr.aws import libsm

tok = json.loads(libsm.get_secret('orcabus/token-service-jwt'))['id_token']
```

## Service User

As an admin, you must register the service user. This has to be done at Cognito AAI terraform stack. Please follow `AdminCreateUser` [flow noted](https://github.com/umccr/infrastructure/pull/412/files) in `users.tf` at upstream infrastructure repo.

After Token Service stack has been deployed, you should then make JSON payload to [put-secret-value](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/secretsmanager/put-secret-value.html) at the following coordinate.

```
orcabus/token-service-user
```

e.g.

```
export AWS_PROFILE=umccr-dev-admin
aws secretsmanager put-secret-value \
    --secret-id "orcabus/token-service-user" \
    --secret-string "{\"username\": \"<snip>\", \"password\": \"<snip>\", \"email\": \"<snip>\"}"
```

After then, the scheduled secret rotation should carry on rotating password, every set days.

---

## Stack

### Rotation Lambda
The stack contains 2 Lambda Python code that do secret rotation. This code is derived from AWS secret manager rotation code template for PostgreSQL. See details in each Python module file docstring. 

### Cognitor
And, there is the thin service layer package called `cognitor` for interfacing with AWS Cognito through boto3 - in fact it just [a façade](https://www.google.com/search?q=fa%C3%A7ade+pattern) of boto3 for Cognito. See its test cases for how to use and operate it.

### Local Dev

#### App

No major dependencies except boto3 which is already avail in the Lambda Python runtime. So, we do not need to package it. For local dev, just create Python venv and, have it boto3 in. 

Do like so:
```
cd lib/workload/stateful/token_service

python -m venv venv
source venv/bin/activate

make install
make test

deactivate
```

#### CDK

The deploy directory contains the CDK code for `TokenServiceStack`. It deploys the rotation Lambdas and, corresponding application artifact using `PythonFunction` (L4?) construct. It runs in the `main-vpc`. And, the secret permissions are bound to the allow resources strictly i.e. see those `grant(...)` flags. It has 1 unit test file and, cdk-nag test through CodePipeline.

Do like so from the repo root:
```
cd ../../../../
```

```
yarn test --- test/stateful/tokenServiceConstruct.test.ts
yarn test --- test/stateful/stateful-deployment.test.ts
yarn test --- test/stateful/
```

```
export AWS_PROFILE=umccr-dev-admin

yarn cdk-stateful ls
yarn cdk-stateful synth -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack
```

Perhaps copy to clipboard and, paste it into VSCode new file buffer and, observe the CloudFormation template being generated.
```
yarn cdk-stateful synth -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack | pbcopy
```

Or

```
mkdir -p .local

yarn cdk-stateful synth -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack > .local/template.yml && code .local/template.yml
```

Then, do CloudFormation lint check:
```
cfn-lint .local/template.yml
```

If that all good, then you may diff e & push straight to dev for giving it the WIP a try...

```
export AWS_PROFILE=umccr-dev-admin
yarn cdk-stateful diff -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack
yarn cdk-stateful deploy -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack
yarn cdk-stateful destroy -e OrcaBusStatefulPipeline/BetaDeployment/OrcaBusStatefulStack/TokenServiceStack
```

Run it in dev, check cloudwatch logs to debug, tear it down; rinse & spin.!

When ready, PR and merge it into the `main` branch to let CodePipeline CI/CD takes care of shipping it towards the `prod`.
