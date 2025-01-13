# This Dockerfile is intended to be used as part of a Docker Compose setup.
# When running this microservice from the Docker Compose root, this Dockerfile
# will build the image, install dependencies, and start the server

FROM public.ecr.aws/docker/library/rust:1.81 AS chef

ENV RUSTC_WRAPPER="/usr/local/cargo/bin/sccache"

WORKDIR /app

RUN apt -y update && apt -y install curl && \
    curl -L --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash
# rustfmt is used for code gen.
RUN cargo binstall -y sccache && cargo binstall -y cargo-chef@0.1.68 && rustup component add rustfmt

FROM chef AS planner

COPY . .
RUN --mount=type=cache,target=/root/.cache/sccache cargo chef prepare

FROM chef AS builder

COPY --from=planner /app/recipe.json recipe.json

# Cargo chef and sccache caches compilation.
RUN --mount=type=cache,target=/root/.cache/sccache cargo chef cook --bin filemanager-api-server && sccache --show-stats

COPY . .
RUN --mount=type=cache,target=/root/.cache/sccache cargo build --bin filemanager-api-server && sccache --show-stats

FROM public.ecr.aws/docker/library/debian:bookworm-slim AS runtime
RUN env

RUN apt -y update && apt -y install curl
COPY --from=builder /app/target/debug/filemanager-api-server /usr/local/bin
ENTRYPOINT ["/usr/local/bin/filemanager-api-server"]
