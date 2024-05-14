# Metadata Manager Deployment Center

The IaC for this microservice is written in AWS CDK Typescript. The deployment stack named `MetadataManagerStack` is in the
`stack.ts` file in the `./deploy` directory. This will construct the relevant resources.

## Architecture

![arch](../docs/architecture.drawio.svg)

To modify the diagram, open the `docs/architecture.drawio.svg` with [diagrams.net](https://app.diagrams.net/?src=about).

## Construct

### APIGW

- Create an API Gateway to be used for this application

### APILambda

- The Lambda is responsible for dealing with API Request from API Gateway

### MigrationLambda

- Responsible for executing migration to the database

### SyncGsheetLambda

- Load tracking sheet data in Google Drive and map it to the Application model
- (PLANNED) periodically trigger the sync every 24 hour
