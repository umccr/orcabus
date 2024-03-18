# Shared Resources

In the stateful world of the OrcaBus we will be sharing some resources so it could be used across microservices.
These resources will be deployed into a stack and will go under the CDK stateful app.

These stateful resources usually have a unique name that could act as an Id for the resource. The unique name will be
defined at the CDK config file where it could be passed in both stateful and stateless stack. The stateless stack can
use the resource by the CDK lookup.

## Database

An Amazon Aurora Serverless PostgreSQL is provisioned to be used across microservices.

A security group is created and available for lookup that could be attached to your compute which allow traffic to the
RDS cluster. The security group name is in the CDK config that your microservice could pass this in as one of the stack props.

Each RDS cluster could contain multiple databases and each microservice is expected to to create their own database and
role to be used in their application. There is a microservice called  `PostgresManager` that specifically handle this administrative
task on PostgreSQL.

RDS IAM is enabled for the cluster, therefore is encouraged to used rather than relying on username-password approach to login to your
database. You could choose the type of the authentication upon creating a role at the RDS when using the `PostgresManager`.

Please check the: [PostgresManager](../../lib/workload/stateless/postgres_manager/README.md)


## Eventbridge
 ... 
