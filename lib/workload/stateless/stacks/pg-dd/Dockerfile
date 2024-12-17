# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM public.ecr.aws/docker/library/python:3.12

RUN pip3 install poetry

WORKDIR /app

COPY . .
RUN poetry install --no-interaction --no-root

ENTRYPOINT ["poetry", "run", "cli"]
