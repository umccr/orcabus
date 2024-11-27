# Data migrate

A service to migrate data between locations.

## Data mover

Locally, use the data mover to move or copy data between locations:

```sh
poetry run dm move --source <SOURCE> --destination <DESTINATION>
```

This command is also deployed as a fargate task which can move data between the 
cache bucket and archive bucket:

Note, if you are deploying this stack manually there may be an issue with docker
failing to login in. A seperate entry for the dev ecr might need to be created in
`~/.docker/config`:

```json
{
  "auths": {
    "843407916570.dkr.ecr.ap-southeast-2.amazonaws.com": {}
  }
}
```

## Local development 

This project uses [poetry] to manage dependencies.

Run the linter and formatter:

```
make check
```

[poetry]: https://python-poetry.org/
[env-example]: .env.example
