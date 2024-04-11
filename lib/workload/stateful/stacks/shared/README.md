# Shared Stack

In the OrcaBus stateful world, we will be deploying a stack that will contain resources that will be shared across
microservices. These resources will generally have a unique name that is passed from the config file, and stacks that
require this resource will be able to look up from by this unique name.


## Database

An Amazon Aurora Serverless PostgreSQL is provisioned to be used across microservices.

RDS cluster could contain multiple databases and each microservice is expected to create its database and
role to be used in its application. There is a microservice called  `PostgresManager` that specifically handles this administrative
task on PostgreSQL.

RDS IAM is enabled for the cluster and, therefore is encouraged to be used rather than relying on username-password approach to log into your database. You could choose the type of authentication upon creating a role at the RDS when using the `PostgresManager`.

Please check the: [PostgresManager](../../../stateless/postgres_manager/README.md)

## Event Source

## Eventbridge

## Schema Registry

## Compute

This construct contains resources that could be shared/attached to a compute resource.

- `SecurityGroup` - The security group that can be attached to compute resources (EC2/lambdas) which has access to the
  database security group.
