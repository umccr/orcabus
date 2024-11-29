# Data migrate

A service to migrate data between locations.

## Data mover

Locally, use the data mover to move or copy data between locations:

```sh
poetry run dm move --source <SOURCE> --destination <DESTINATION>
```

This command is also deployed as a fargate task triggered by step functions.
The step functions expects as input a JSON which specifies the command (move or copy),
a source and a destination. For example, to move a specified `portalRunId` into the archive
bucket (this is probably easier in the step functions console):

```sh
export ARN=$(aws stepfunctions list-state-machines | jq -r '.stateMachines | .[] | select(.name == "orcabus-data-migrate-mover") | .stateMachineArn')
export COMMAND="move"
export SOURCE="s3://umccr-temp-dev/move_test_2"
export DESTINATION="s3://filemanager-inventory-test/move_test_2"
aws stepfunctions start-execution --state-machine-arn $ARN  --input "{\"command\" : \"$COMMAND\", \"source\": \"$SOURCE\", \"destination\": \"$DESTINATION\" }"
```

## Local development 

This project uses [poetry] to manage dependencies.

Run the linter and formatter:

```
make check
```

[poetry]: https://python-poetry.org/
[env-example]: .env.example
