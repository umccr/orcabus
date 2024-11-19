# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM public.ecr.aws/docker/library/python:3.12

ARG POETRY_VERSION=1.8
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY . .
RUN poetry install --no-root

ENTRYPOINT ["/bin/bash", "-c", "make", "local"]