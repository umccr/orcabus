# SRM Deploy

This directory contains CDK code that will be called and assembled by higher level class such as `lib/workload/stateless/statelessStackCollectionClass.ts`.

Collectively, all CDK constructs created under this `deploy` directory forms as **one deployable stack**. Hence, just  a single `stack.ts` file should suffice if your app deployment is simple.

## TL;DR

Go back to repo root:

```
cd ../../../../../
```

Hot-deploy against dev:
```
export AWS_PROFILE=umccr-dev-admin

yarn cdk-stateless list
yarn cdk-stateless synth -e OrcaBusStatelessPipeline/OrcaBusBeta/SequenceRunManagerStack
yarn cdk-stateless diff -e OrcaBusStatelessPipeline/OrcaBusBeta/SequenceRunManagerStack
yarn cdk-stateless deploy -e OrcaBusStatelessPipeline/OrcaBusBeta/SequenceRunManagerStack
yarn cdk-stateless destroy -e OrcaBusStatelessPipeline/OrcaBusBeta/SequenceRunManagerStack
```

CloudFormation template:
```
yarn cdk-stateless synth -e OrcaBusStatelessPipeline/BetaDeployment/SequenceRunManagerStack > .local/template.yml
cfn-lint .local/template.yml
code .local/template.yml
```

CDK test:
```
yarn test --- test/stateless/deployment.test.ts
yarn test --- test/stateless/
```
