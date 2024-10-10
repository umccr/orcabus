# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM public.ecr.aws/docker/library/rust:1.81 AS chef

ARG DATABASE_URL
ENV DATABASE_URL $DATABASE_URL

WORKDIR /app

# rustfmt is used for code gen.
RUN cargo install cargo-chef && rustup component add rustfmt

FROM chef AS planner

COPY . .
RUN cargo chef prepare

FROM chef AS builder

COPY --from=planner /app/recipe.json recipe.json

# Cargo chef caches compilation.
RUN cargo chef cook

COPY . .
RUN cargo build --bin filemanager-api-server

FROM public.ecr.aws/docker/library/debian:bookworm-slim AS runtime

# curl is used for healthcheck.
RUN apt -y update && apt -y install curl

COPY --from=builder /app/target/debug/filemanager-api-server /usr/local/bin
ENTRYPOINT ["/usr/local/bin/filemanager-api-server"]
