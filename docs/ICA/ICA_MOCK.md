# ICA Mock Service

Using through `libica` or otherwise, any calling to ICA interfacing logic will be instrumented with these mock services for testing purpose.

## ICA v1 Mock Service

From project root, preform:
```
make up
make ps
```

### WES

- In one terminal, monitor WES endpoint as follows.
```
docker logs orcabus_wes -f 
[11:05:13 AM] › [CLI] …  awaiting  Starting Prism…
[11:05:40 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/workflows
[11:05:40 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/workflows
[11:05:40 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/workflows/nisi
[11:05:40 AM] › [CLI] ✔  success   PATCH      http://0.0.0.0:4010/v1/workflows/alias
[11:05:40 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/workflows/runs
[11:05:41 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/workflows/runs/architecto
[11:05:41 AM] › [CLI] ✔  success   PUT        http://0.0.0.0:4010/v1/workflows/runs/tenetur:abort
[11:05:41 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/workflows/runs/ea/history
...
[11:05:41 AM] › [CLI] ✔  success   Prism is listening on http://0.0.0.0:4010
```

- Open another terminal, query mock REST endpoint as follows.
```
curl -s -H "Authorization: Bearer Test" -X GET http://localhost/v1/workflows | jq
curl -s -H "Authorization: Bearer Test" -X GET http://localhost/v1/workflows/wfr.123456789abcd | jq
```

### GDS

- Similarly.

```
docker logs orcabus_gds -f
[11:05:13 AM] › [CLI] …  awaiting  Starting Prism…
[11:05:43 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/files/dolore
[11:05:43 AM] › [CLI] ✔  success   PATCH      http://0.0.0.0:4010/v1/files/dolores
[11:05:43 AM] › [CLI] ✔  success   DELETE     http://0.0.0.0:4010/v1/files/modi
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files
[11:05:43 AM] › [CLI] ✔  success   PATCH      http://0.0.0.0:4010/v1/files
[11:05:43 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/files
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files/list
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files/copy
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files/minus:completeUpload
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files/et:archive
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/files/dolorem:unarchive
[11:05:43 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/folders
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/folders
[11:05:43 AM] › [CLI] ✔  success   PATCH      http://0.0.0.0:4010/v1/folders
...
[11:05:43 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/volumes
[11:05:43 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/v1/volumes
[11:05:43 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/v1/volumes/voluptas
[11:05:43 AM] › [CLI] ✔  success   PATCH      http://0.0.0.0:4010/v1/volumes/consequuntur
[11:05:43 AM] › [CLI] ✔  success   DELETE     http://0.0.0.0:4010/v1/volumes/tenetur
[11:05:43 AM] › [CLI] ✔  success   Prism is listening on http://0.0.0.0:4010
```

- Open another terminal, query mock REST endpoint as follows.
```
curl -s -H "Authorization: Bearer Test" -X GET http://localhost/v1/files | jq
```

```
curl -s -H "Authorization: Bearer Test" -X GET 'http://localhost/v1/files?volume.name=anything&path=/work/for/hitting/prism/dynamic/mock' | jq
```

## ICA v2 Mock Service

Yup. Same.

```
docker logs orcabus_ica_v2 -f          
[11:12:40 AM] › [CLI] …  awaiting  Starting Prism…
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/analysisStorages
[11:13:13 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/api/bundles
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/bundles/et
[11:13:13 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/api/bundles/magni:release
...
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/notificationChannels
[11:13:13 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/api/notificationChannels
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/notificationChannels/sit
[11:13:13 AM] › [CLI] ✔  success   PUT        http://0.0.0.0:4010/api/notificationChannels/aspernatur
[11:13:13 AM] › [CLI] ✔  success   DELETE     http://0.0.0.0:4010/api/notificationChannels/exercitationem
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/pipelines
...
[11:13:13 AM] › [CLI] ✔  success   POST       http://0.0.0.0:4010/api/projects
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/projects/architecto
[11:13:13 AM] › [CLI] ✔  success   PUT        http://0.0.0.0:4010/api/projects/ducimus
[11:13:13 AM] › [CLI] ✔  success   GET        http://0.0.0.0:4010/api/projects/doloremque/bundles
...
[11:13:13 AM] › [CLI] ✔  success   Prism is listening on http://0.0.0.0:4010
```

- Open another terminal, query mock REST endpoint as follows.
```
curl -s -H "Authorization: Bearer Test" -X GET http://localhost/api/bundles | jq
```

```
curl -s -H "Authorization: Bearer Test" -X GET http://localhost/api/projects | jq
```
