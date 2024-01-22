# OrcaBus

UMCCR Orchestration Bus that leverage AWS EventBridge as Event Bus to automate the BioInformatics Workflows Pipeline.

## CDK

At the top level, the Git repository root is _the CDK TypeScript project_. It is bootstrapped with `cdk init orcabus --language typescript`. Therefore, the outer level codebase is the single CDK infrastructure application. 

Please note; this is the _INVERSE_ of some typical standalone project setup such that the repo root of the project is your app toolchain codebase and the deployment code are arranged under some arbitrary subdirectory like `./deploy/<cdk app root>`. We **do not** do this in this repo as we anticipate that we are going to deploy multiple of closely related micro applications.

In this repo, we flip this view such that the Git repo root is the TypeScript CDK project; that wraps our applications into `./lib/` directory. You may [sparse checkout](https://git-scm.com/docs/git-sparse-checkout) or directly open subdirectory to set up the application project alone if you wish; e.g. `webstorm lib/workload/stateless/metadata_manager` or `code lib/workload/stateless/metadata_manager` or `pycharm lib/workload/stateless/sequence_run_manager` or `rustrover lib/workload/stateless/filemanager`. However, `code .` is a CDK TypeScript project.

This root level CDK app contains 3 major stacks: `pipeline`, `stateful` and `stateless`. Pipeline stack is the CI/CD automation with CodePipeline setup. The `stateful` stack holds and manages some long-running AWS infrastructure resources. The `stateless` stack manages self-mutating CodePipeline reusable CDK Constructs for the [MicroService Applications](docs/developer/MICROSERVICE.md). In terms of CDK deployment point-of-view, the microservice application will be "stateless" application such that it will be changing/mutating over time; whereas "the data" its holds like PostgreSQL server infrastructure won't be changing that frequent. When updating "stateful" resources, there involves additional cares, steps and ops-procedures such as backing up database, downtime planning and so on; hence stateful. We use [configuration constants](./config) to decouple the reference between `stateful` and `stateless` AWS resources.

In most cases, we deploy with automation across operational target environments or AWS accounts: `beta`, `gamma`, `prod`. For some particular purpose (such as onboarding procedure, isolated experimentation), we can spin up the whole infrastructure into some unique isolated AWS account. These key CDK entrypoints are documented in the following sections: Automation and Manual.

### Automation

_CI/CD through CodePipeline automation from AWS toolchain account_

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

_manual deploy to an isolated specific AWS account_

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

## Development

_Heads up: Polyglot programming environment. We shorten some trivial steps into `Makefile` target. You may deduce step-by-step from `Makefile`, if any._

### Typography

When possible, please use either `OrcaBus` (camel case) or `orcabus` (all lower case).

### Toolchain

_Setting up baseline toolchain_

```
docker --version
Docker version 24.0.7, build afdd53b

node -v
v18.19.0

npm i -g yarn
yarn -v
3.5.1
```

Additionally, we expect the following common tools be installed and available in your system shell PATH. We provide [Brewfile](Brewfile) as an example. You may manage these common tools in any other way as see fit for your local setup.

```
brew bundle
```

### Mocking

- We use docker compose as a mock stack for application local dev and running test suite purpose.
- Typically, you will have your own application compose stack defined at your app project root, if any.
- You can also reuse common docker compose stack, if applicable. See [shared/README.md](shared)

### Microservice

- See [docs/developer/MICROSERVICE.md](docs/developer/MICROSERVICE.md)

### Lint

- Run lint: `yarn lint`
- Fix lint issue: `yarn lint-fix`
- Opt-out lint: See [.eslintignore](.eslintignore)

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

We have GitHub Action workflow to reinforce Lint, Code Formatting and Pre-commit Hook check as [Pull Request Build](.github/workflows/prbuild.yml) pipeline before main CI/CD automation run at CodePipeline. This is to protect any accidental secrets leak and/or pre-flight check for CI/CD automation. 

### IDE

- Visual Studio Code, JetBrains IDE
- Code style
  - no tab
  - indent with `2` spaces for JS/TS/JSON/YAML
  - indent with `4` spaces for Python
- For Visual Studio Code, the following extensions are recommended
  - [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
  - [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)
