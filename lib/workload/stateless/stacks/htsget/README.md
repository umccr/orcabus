# htsget stack

This stack deploys [htsget-rs] to access files. Any files accessible by filemanager are also accessible using htsget.

The deployed instance of the htsget-rs can be reached using stage at `https://htsget-file.<stage>.umccr.org`
and the orcabus API token. To retrieve the token, run:

```sh
export TOKEN=$(aws secretsmanager get-secret-value --secret-id orcabus/token-service-jwt --output json --query SecretString | jq -r 'fromjson | .id_token')
```

Then, the API can be queried:

```sh
curl -H "Authorization: Bearer $TOKEN" "https://htsget-file.dev.umccr.org/reads/service-info" | jq
```

[htsget-rs]: https://github.com/umccr/htsget-rs