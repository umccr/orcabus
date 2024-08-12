# filemanager-api-server

An instance of the filemanager api which can be launched as a webserver. The default address which the webserver uses
is `0.0.0.0:8000`. Set the `FILEMANAGER_API_SERVER_ADDR` environment variable to change this. To run the local server:

```sh
make start
```

Then, checkout the OpenAPI docs at: `http://localhost:8000/swagger-ui`.