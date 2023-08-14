# Metadata manager

The `MetadataManager` is one of the microservice within the UMCCR OrcaBus that manages the metadata records used for the
BioInformatics pipelines. The service will be responsible to make records to stay up to date and able to sync records
from multiple sources.

## Development

### Git Checkout
As this microservice is part of a monorepo from the main OrcaBus project, the process Git Flow process
will follow on the root of this project.

### Development

#### Setup

Change the terminal directory from the OrcaBus root to this directory:

```
cd lib/workload/stateless/metadata_manager/src
```

Requirement for this project:
  - nodejs
  - edgedb (see <https://www.edgedb.com/install>)

To install the dependency of this project
```
yarn
```

#### Build
```yarn edgetypes```


### Run
```yarn watch```

#### Testing
```yarn test```
