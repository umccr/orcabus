# CDK constructs for filemanager

This folder contains CDK constructs for filemanager which is used by the outer project 
to instantiate and deploy filemanager.

## Overview

The primary component that is deployed in filemanager is Lambda functions for each of the lambda
crates within this project. This, alongside the shared database in Orcabus allows the filemanager
to perform file ingestion, querying, etc.

### Inputs

The filemanager operates on S3 buckets, and expects queues as input which can recieve S3 events. It also requires
the bucket names to create policies that allow S3 's3:List*' and 's3:Get*' operations. These operations are used to
fetch additional object data such as storage classes.

### Migration

The filemanager expects a dedicated database within the shared database cluster, which it can use to store data.
Initially, the filemanager-migrate-lambda function is deployed to perform database table migrations using the
cdk_resource_invoke.ts construct. Then, the other Lambda functions are deployed normally within the filemanager
construct.
