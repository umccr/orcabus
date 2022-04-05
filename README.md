# OrcaBus

UMCCR Orchestration Bus that leverage AWS EventBridge as Event Bus to automate the BioInformatics Workflows Pipeline.

## Quickstart

### Pre-requisites

```
brew tap aws/tap
brew install aws-sam-cli

sam --version
SAM CLI, version 1.43.0

npm install -g aws-cdk

cdk version
2.19.0 (build e0d3e62)
```

### Pre-commit hooks

We are using pre-commit hooks to check for any secret-key leaks and for linting purposes.
Check [UMCCR wiki](https://github.com/umccr/wiki/blob/master/computing/dev-environment/git-hooks.md) for details.

```
brew install pre-commit detect-secrets

pre-commit --version
pre-commit 2.18.1

detect-secrets --version
1.2.0
```

### Development

- Create Python environment; we recommend conda or mamba.

```
conda create -n orcabus python=3.9
conda activate orcabus

python -V
Python 3.9.12

make install
make check
make run
```

### Build & Deploy

```
make build
cdk diff
make deploy
```

## Current mock event handling

The mock setup consists of two stacks:
- oen to configure the event bus and event schemas used by the application
- the other to manage the application itself

The application is a series of Lambda function that produce/consume events from the event bus. Two Lambdas have a special role, as they provide the interface with external services (ICA ENS/WES).

### Lambdas
Functions to prepare WES workflow executions. These functions normally receive events from the orchestrator, signaling a specific state has been reached and further actions can be triggered
- bcl_convert (prepare BCL Convert WES workflow)
- dragen_wgs_qc (prepare DRAGEN WGS QC WES workflow)
- dragen_wgs_somatic (prepare DRAGEN WGS SOMATIC WES workflow)

Functions as interface to external services
- ens_event_manager (manage events received by ICA ENS via SQS. Its job is to translate external events into internal ones, check event consistency/duplication and persist the current state)
- wes_launcher (send WES execution requests to ICA. Its job to interface with the ICA WES service and launch requested WES workflows) NOTE: the mock version will instead send SQS formatted events directly to the ens_event_manager

- orchestrator (manage and distribute events as needed, based on external triggers and internal state. Its job is to react to external events and decide which, if any, action to take)
- gds_manager {file level event monitor; may not be needed if functionality is covered by ens_event_manager}

Schemas:
- SequenceRunStateChange (internal version of ENS `bssh.runs` events; represents a change in sequencing state; emitted by ens_event_manager)
- WorkflowRunStateChange (internal version of ENS `wes.runs` events; represents a change in workflow state; emitted by ens_event_manager)
- WesLaunchRequest (event to request a WES workflow launch; usually emitted by workflow prep lambdas)
- WorkflowRequest (event to trigger a workflow prep lambda, may/may not result in WES workflow request)


#### Layers
Lambda layers are used to make common libs (like utils and schema) available to all Lambdas.


## Possible next steps

    1. Ask illumina to have a partner event source integration for ICA with AWS EventBridge. It would cleanup the microservices integration, for instance: instead of connecting SQS queues between accounts, providing an API abstraction that can be consumed/reused in multiple ways.
    1. Add an extra target that dumps the GDS event in DynamoDB, perhaps a first step to get rid of the heavy Django ORM abstraction.
