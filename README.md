# OrcaBus

UMCCR Orchestration Bus that leverage AWS EventBridge as Event Bus to automate the BioInformatics Workflows Pipeline.

## Development

```
conda create -n orcabus python=3.9
conda activate orcabus

make install
make test

npx cdk list
npx cdk synth OrcaBusStatefulStack
npx cdk synth
npx cdk diff
npx cdk deploy OrcaBusStatefulStack
npx cdk deploy --all
```
