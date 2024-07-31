# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM lukemathwalker/cargo-chef:latest-rust-1 AS chef

ARG DATABASE_URL
ENV DATABASE_URL $DATABASE_URL

WORKDIR /app

# rustfmt is used for code gen.
RUN rustup component add rustfmt

FROM chef AS planner

COPY . .
RUN cargo chef prepare

FROM chef AS builder

COPY --from=planner /app/recipe.json recipe.json

# Cargo chef caches compilation.
RUN cargo chef cook

COPY . .
# This must be release so that swagger_ui can work.
# See https://github.com/juhaku/utoipa/issues/527.
RUN cargo build --release --bin filemanager-api-server

FROM debian:bookworm-slim AS runtime

# curl is used for healthcheck.
RUN apt -y update && apt -y install curl

COPY --from=builder /app/target/release/filemanager-api-server /usr/local/bin
ENTRYPOINT ["/usr/local/bin/filemanager-api-server"]
