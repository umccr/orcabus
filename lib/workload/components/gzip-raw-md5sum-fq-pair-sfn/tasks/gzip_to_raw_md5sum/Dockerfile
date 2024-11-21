FROM --platform=${TARGETPLATFORM} ubuntu:noble

ARG TARGETPLATFORM

RUN \
  apt update -y -q && \
  apt upgrade -y -q && \
  if [ "${TARGETPLATFORM#linux/}" = "arm64" ]; then \
    platform_url="aarch64";  \
  else \
    platform_url="x86_64"; \
  fi && \
  apt update -yq && \
  apt upgrade -yq && \
  apt install -yq \
    wget \
    jq \
    tar \
    gzip \
    unzip \
    pigz \
    python3.12 \
    python3-pip && \
  python3 -mpip install wrapica --break-system-packages && \
  wget \
    --quiet \
    --output-document "awscliv2.zip" \
    "https://awscli.amazonaws.com/awscli-exe-linux-${platform_url}.zip" && \
  unzip -q "awscliv2.zip" && \
  ./aws/install && \
  rm "awscliv2.zip"

# Copy the scripts to the docker container
# Make the scripts executable
COPY scripts/ scripts/
RUN chmod +x scripts/*

# Copy the docker entrypoint to the docker container
COPY docker-entrypoint.sh docker-entrypoint.sh
# Make the docker entrypoint executable
RUN chmod +x "./docker-entrypoint.sh"

# Set the entrypoint as the docker entrypoint script
CMD [ "./docker-entrypoint.sh" ]

