# OrcaBus

UMCCR Orchestration Bus that leverage AWS EventBridge as Event Bus to automate the BioInformatics Workflows Pipeline.

## Development

### Toolchain

```
docker --version
>Docker version 23.0.5

conda create -n orcabus python=3.10
conda activate orcabus
python -V
>Python 3.10.10

node -v
>v16.15.0
```

### TL;DR

_Heads up: Polyglot programming environment. So we wrap couple of different tool trivial steps into Makefile target as one-go shortcut! You may deduce step-by-step from Makefile, if any._

```
make install
make check
make test
make build

yarn cdk list
yarn cdk synth OrcaBusStatefulStack
yarn cdk diff OrcaBusStatefulStack
yarn cdk deploy OrcaBusStatefulStack

yarn cdk synth
yarn cdk diff
yarn cdk deploy --all
```

### Lint

- Run lint: `yarn lint`
- Fix lint issue: `yarn lint-fix`

### Code Formatting

TypeScript
- Run prettier: `yarn prettier`
- Fix prettier issue: `yarn prettier-fix`

Python
- Run black: `yarn black`
- Fix black issue: `yarn black-fix`

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
