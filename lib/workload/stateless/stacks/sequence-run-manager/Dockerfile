# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM public.ecr.aws/docker/library/python:3.12

WORKDIR /app

COPY . .

RUN make install

ENTRYPOINT ["make", "start"]
