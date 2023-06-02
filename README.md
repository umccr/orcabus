# OrcaBus

UMCCR Orchestration Bus that leverage AWS EventBridge as Event Bus to automate the BioInformatics Workflows Pipeline.

## Development

_Heads up: Polyglot programming environment. We shorten some trivial steps into `Makefile` target. You may deduce step-by-step from `Makefile`, if any._

### Typography

When possible, please use either `OrcaBus` (camel case) or `orcabus` (all lower case).

### Toolchain

```
docker --version
Docker version 24.0.1, build 680212238b

conda create -n orcabus python=3.10
conda activate orcabus
python -V
Python 3.10.11

node -v
v18.16.0

npm i -g yarn
yarn -v
3.5.1
```

### MySQL

```
make up
make ps
make mysql
mysql> show databases;
mysql> use orcabus;
mysql> show tables;
mysql> \q
```

### Creating Microservice

Two high level tasks. As follows.

#### 1. Bootstrap using Skel Profile

- [DJANGO_API.md](docs/developer/DJANGO_API.md)
- [DJANGO_PROC.md](docs/developer/DJANGO_PROC.md)

#### 2. Infrastructure as Code for microservice

- Encourage to use CDK as much as possible.
- You could write one CDK construct from scratch. However, prefer use Construct Library whenever possible.
- In the order of preference; please browse and make use of Construct patterns from the following.
  1. https://docs.aws.amazon.com/solutions/latest/constructs/welcome.html
  2. https://serverlessland.com
  3. https://constructs.dev
- Please check existing microservice implementations for reference.

For example, to use https://docs.aws.amazon.com/solutions/latest/constructs/aws-cognito-apigateway-lambda.html

- At project root, execute as follows:
```
yarn add @aws-solutions-constructs/aws-cognito-apigateway-lambda
```

- Or, to remove:
```
yarn remove @aws-solutions-constructs/aws-cognito-apigateway-lambda
```

### Automation

_aka CDK Pipeline or CI-CD through CodePipeline in Toolchain Account_

```
make install
make check
make test

yarn cdk list

yarn cdk synth <StackName>
yarn cdk diff <StackName>
yarn cdk deploy <StackName>

yarn cdk synth
yarn cdk diff
yarn cdk deploy --all
```

### Manual

_this is manual deploy to an isolated specific DEV account_

```
export AWS_PROFILE=dev

make install
make check
make test

yarn orcabus --help

yarn orcabus list
yarn orcabus synth OrcaBusStatefulStack
yarn orcabus diff OrcaBusStatefulStack
yarn orcabus deploy OrcaBusStatefulStack
yarn orcabus deploy --all
yarn orcabus destroy --all
```

### Lint

- Run lint: `yarn lint`
- Fix lint issue: `yarn lint-fix`

### Code Formatting

TypeScript
- Run prettier: `yarn prettier`
- Fix prettier issue: `yarn prettier-fix`

Python
- Run code formatter: `yarn black`
- Fix code format issue: `yarn black-fix`

### Audit

- Run `yarn audit` for package security vulnerabilities
- Recommend fixing/updating any package with _direct_ dependencies
- If vulnerabilities found in transitive dependency, but it has yet to resolve, then list them in `package.json > resolutions` node as [Selective Dependency Resolutions condition explained here](https://classic.yarnpkg.com/en/docs/selective-version-resolutions/).

### Pre-commit Hook

> NOTE: We use [pre-commit](https://github.com/umccr/wiki/blob/master/computing/dev-environment/git-hooks.md). It will guard and enforce static code analysis such as `lint` and any security `audit` via pre-commit hook. You are encouraged to fix those. If you wish to skip this for good reason, you can by-pass [Git pre-commit hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) by using `git commit --no-verify` flag.

```commandline
git config --unset core.hooksPath
pre-commit install
pre-commit run --all-files
```

### IDE

- Recommended to use JetBrains IDE
- Code style
  - no tab
  - indent with `2` spaces for JS/TS/JSON/YAML
  - indent with `4` spaces for Python
- For Visual Studio Code, the following extensions are recommended
  - [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
  - [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
