# Microservice

There are two high level tasks.

1. **uApp** : create your app using your favourite dev stack and toolchain. This should typically be in `./lib/workload/stateless/`
2. **CDK**  : write up the deployment "CDK Construct" of your app; to wire up with the root level infrastructure "CDK App".

> NOTE: 
> * We only have one CDK project at outer level of the Git repository root; i.e. a CDK project in TypeScript. 
> 
> * Nested CDK projects are discouraged to avoid confusion. If you need a specific CDK `App()` object instance for some experimentation, say building a `demo` CDK app, you can instantiate one through project root level `./bin/demo.ts` and, assemble your demo CDK Stack/Construct(s) under `./lib/` directory. Then, wire up as `yarn` target in project root `package.json > script` entry e.g. `"demo": "cdk --app 'npx ts-node --prefer-ts-exts bin/demo.ts'",` Then, call as `yarn demo list` and `yarn demo deploy --all` and so on so ford.

Either tasks _(developing an app and/or cdk deployment constructs)_; we promote code reuse for some boilerplate and common best practise patterns. Please give time to read articles/concepts in the `Reading` section below for developer background technical alignment. We also share knowledge-based (KB) discussion, revise and harmonise these high level technical concepts through our routine OrcaBus catchup meetings.

## uApp

_uApp = microservice app_

### Native Bootstrap

You may also just simply use "native toolchain boostrap" method. This could be the typical "getting started" of respective tool or framework. Some examples as follows.

```
cargo init
npx tsc --init
django-admin startproject
...
...
<etc>
```

### Bootstrap using Skel Profile

The "skel" profile are one abstraction up; from the native toolchain application bootstrapping method; such that you help your peer developer to fast track with some boilerplate code and common setup; up to speed. 

Think of; it is "the origin" of where your _now_ very complex application to date in near future. Doing this way is optional. We may revise whether this skel approach is useful in the future iterations.

- [DJANGO_API.md](DJANGO_API.md)
- [DJANGO_PROC.md](DJANGO_PROC.md)
- [RUST_API.md](RUST_API.md)

### AWS Native

> Q. My microservice app is an "AWS native app" with StepFunction and/or DynamoDB, then what?
> 
> A. That would mean it is just a CDK TypeScript construct code arrange under `./lib/workload/stateless/<your AWS native app>` directory as an infrastructure stateless component. In this case, you may leverage [Localstack compose stack](../../shared/MOCK_AWS.md) and/or chosen AWS SDK (e.g. Boto3/Python or `awslocal` CLI in bash script) for local dev, mocking and unit testing purpose.


## CDK

Since it is the single CDK Project, all CDK dependencies are managed centrally at `package.json` at the Git repo project root and, the CDK CLI version is harmonised with localised Node.js execution through Yarn e.g. `yarn cdk list`. With this way, every developer's local dev environment and, automation CodePipeline environment will have the same CDK version, enforced.

### Infrastructure as Code for microservice

- Encourage to use CDK with TypeScript.
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

## Reading

1. https://trello.com/c/KDVIxQfm/1407-orcabus-v1-capture-high-level-orcabus-design-tech-choices
2. https://microservices.io/patterns/microservice-chassis.html
3. https://docs.aws.amazon.com/whitepapers/latest/microservices-on-aws/microservices-on-aws.html
4. https://www.google.com/search?q=mono+repo
5. https://docs.aws.amazon.com/cdk/v2/guide/core_concepts.html
6. https://www.google.com/search?q=cdk+stateful+stateless
7. https://www.google.com/search?q=cdk+app+vs+stack+vs+construct
