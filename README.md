# OrcaBus

UMCCR OrcaBus (Orchestration Bus) leverages AWS EventBridge as an Event Bus to automate the BioInformatics Workflows Pipeline.

## CDK

At the top level, the Git repository root is _the CDK TypeScript project_. It is bootstrapped with `cdk init orcabus --language typescript`. Therefore, the outer level codebase is the single CDK infrastructure application. 

Please note; this is the _INVERSE_ of some typical standalone project setup such that the repo root of the project is your app toolchain codebase and the deployment code are arranged under some arbitrary subdirectory like `./deploy/<cdk app root>`. We **do not** do this in this repo as we anticipate that we are going to deploy multiple of closely related micro applications.

In this repo, we flip this view such that the Git repo root is the TypeScript CDK project; that wraps our applications into `./lib/` directory. You may [sparse checkout](https://git-scm.com/docs/git-sparse-checkout) or directly open subdirectory to set up the application project alone if you wish; e.g. `webstorm lib/workload/stateless/stacks/metadata-manager` or `code lib/workload/stateless/stacks/metadata-manager` or `pycharm lib/workload/stateless/stacks/sequence-run-manager` or `rustrover lib/workload/stateless/stacks/filemanager`. However, `code .` is a CDK TypeScript project.

There are 2 CDK apps here:

- Stateful
  
  This holds and manages long-running AWS stateful resources. The resources will typically be something that won't be
  changing frequently and could not be torn down easily. For example, the RDS Cluster which contains application data. When
  updating "stateful" resources, additional care is needed such as backing up the database, downtime planning and so on;
  hence stateful.

- Stateless

  As the opposite of stateful resources, stateless resources will have the ability to redeploy quickly without worrying
  about any retainable data. For example, AWS lambdas and API Gateway have no retainable data when destroyed and spin up
  easily. The [Microservice Applications](docs/developer/MICROSERVICE.md) resources will usually be here and they will
  have a lookup from stateful resources when needed.

You could access the CDK command for each app via `yarn cdk-stateless` or `yarn cdk-stateful`. The `cdk-*` is
just a CDK alias that points to a specific app, so you could use `cdk` command natively for each app (e.g. `yarn cdk-stateless --help`).

We use [configuration constants](./config) to reference constants between the `stateful` and `stateless` CDK apps.

In most cases, we deploy with automation across operational target environments or AWS accounts: `beta` (dev), `gamma` (staging),
`prod`. For some particular purpose (such as onboarding procedure, or isolated experimentation), we can spin up the
whole infrastructure into some unique isolated AWS account.

### Automation

_CI/CD through CodePipeline automation from the AWS toolchain account_

There are 2 pipeline stacks in this project, one for the `stateful` and one for the `stateless` stack deployment. Both
pipelines are triggered from the `main` branch and configured as a self-mutating pipeline. The pipeline will automatically deploy
CDK changes from `beta` -> `gamma` -> `prod` account, where each transition has an approval stage before deploying to the next account.

To access the pipeline's CDK you could do it within the app stack with the pipeline name either be
`OrcaBusStatelessPipeline` or `OrcaBusStatefulPipeline` (e.g. `yarn cdk-stateless
OrcaBusStatelessPipeline`).

In general, you do **NOT** need to touch the pipeline stack at all, as changes to the deployment stack will be taken care of
by the self-mutating pipeline. You might need to touch if there is a dependency in any of the build processes (unit
testing or `cdk synth` ). For example, Rust installation is required to build the lambda asset.

```sh
# prerequisite before running cdk command to the OrcaBus Pipeline
make install
make test # This will test all tests available in this repo

# accessing the stateless pipeline with cdk
yarn cdk-stateless synth OrcaBusStatelessPipeline
yarn cdk-stateless diff OrcaBusStatelessPipeline
yarn cdk-stateless deploy OrcaBusStatelessPipeline

# or for stateful pipeline
yarn cdk-stateful synth OrcaBusStatefulPipeline
yarn cdk-stateful diff OrcaBusStatefulPipeline
yarn cdk-stateful deploy OrcaBusStatefulPipeline
```

The pipeline is deployed on the toolchain/build account (bastion in the UMCCR AWS account).

### Manual

_manual deployment from local computer to AWS account_

You may want to see your resources deployed quickly without relying on the pipeline to do it for you. You could do so by
deploying to the `beta` account by specifying the stack name with the relevant AWS Credentials.

You could use the `yarn cdk-stateless --help` command described above to deploy the microservice. Remember you use the credential to
where the resource will be deployed and **NOT** the pipeline (toolchain) credential.

You could list the CDK stacks with the `yarn cdk-stateless list` command to look at the stack ID given to your microservice app.

```sh
yarn cdk-stateless list

OrcaBusStatelessPipeline
OrcaBusStatelessPipeline/OrcaBusBeta/MetadataManagerStack
...
```

For example, deploying the metadata manager stateless resources directly from your computer as follows.

```sh
yarn cdk-stateless synth -e OrcaBusStatelessPipeline/OrcaBusBeta/MetadataManagerStack
yarn cdk-stateless diff -e OrcaBusStatelessPipeline/OrcaBusBeta/MetadataManagerStack
yarn cdk-stateless deploy -e OrcaBusStatelessPipeline/OrcaBusBeta/MetadataManagerStack
```

NOTE: If you deployed manually and the pipeline starts running (e.g. a new commit at the source branch) your stack will be overridden to what you have in the main branch. You are encouraged to look around `README.md` and `Makefile` of existing service stacks (both stateful/stateless) to adapt from existing setup.

## Development

_Heads up: Polyglot programming environment. We shorten some trivial steps into `Makefile` target. You may deduce step-by-step from `Makefile`, if any._

To develop your microservice application, please read: 
- [microservice guide](docs/developer/MICROSERVICE.md) 
- [event schema guide](docs/schemas/README.md)
- [shared resource guide](./lib/workload/stateful/stacks/shared/README.md)

### Typography

When possible, please use either `OrcaBus` (camel case) or `orcabus` (all lower case).

#### Typescript

When using typescript we will use the convention defined in [AWS
Guide](https://docs.aws.amazon.com/prescriptive-guidance/latest/best-practices-cdk-typescript-iac/typescript-best-practices.html#naming-conventions).

- Use camelCase for variable and function names.
- Use PascalCase for class names and interface names.
- Use camelCase for interface members.
- Use PascalCase for type names and enum names.
- Name files with camelCase (for example, ebsVolumes.tsx or storage.tsb)

For folder name, we will be using `kebab-case` as this is the common convention in TypeScript project.

### Toolchain

_Setting up baseline toolchain_

```
docker --version
Docker version 26.1.4, build 5650f9b

node -v
v20.14.0

npm i -g yarn
yarn -v
4.3.0
```

Additionally, we expect the following common tools be installed and available in your system shell PATH. We provide [Brewfile](Brewfile) as an example. You may manage these common tools in any other way as see fit for your local setup.

```sh
brew bundle
```
  
### Mocking

- We use docker-compose as a mock stack for application local dev and running test suite purpose.
- Typically, you will have your own application compose stack defined at your app project root, if any.
- You can also reuse a common docker compose stack, if applicable. See [shared/README.md](shared)

### Microservice

- See [docs/developer/MICROSERVICE.md](docs/developer/MICROSERVICE.md)

### Lint

- Run lint: `yarn lint`
- Fix lint issue: `yarn lint-fix`
- Opt-out lint: See [eslint.config.mjs](eslint.config.mjs)

### Code Formatting

TypeScript

- Run prettier: `yarn prettier`
- Fix prettier issue: `yarn prettier-fix`
- Opt-out prettier: See [.prettierignore](.prettierignore)

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

### GitHub Action

#### Lint-Formatting-Security

We have GitHub Action workflow to reinforce Lint, Code Formatting and Pre-commit Hook check as [Pull Request
Build](.github/workflows/prbuild.yml) pipeline before the main CI/CD automation run at CodePipeline. This is to protect any
accidental secrets leak and/or pre-flight check for CI/CD automation.

#### Testing

We have enabled application unit tests and stack security compliance in our GitHub Actions workflow using
AWS CodeBuild as the runner. This provides developers with faster feedback before merging changes into the main branch.
The deployment pipeline will run all tests again before deployment. If you believe your commit doesn't
require GitHub Actions testing, you can include the `[skip ci]` in your commit message to skip this step.

### IDE

- Visual Studio Code, JetBrains IDE
- Code style
  - no tab
  - indent with `2` spaces for JS/TS/JSON/YAML
  - indent with `4` spaces for Python
- For Visual Studio Code, the following extensions are recommended
  - [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
  - [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
