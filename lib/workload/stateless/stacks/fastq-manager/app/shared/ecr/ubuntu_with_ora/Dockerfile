FROM ubuntu:noble

LABEL maintainer="Alexis Lucattini"

ARG TARGETPLATFORM

ARG ORAD_REF_DOWNLOAD_URL="https://s3.amazonaws.com/webdata.illumina.com/downloads/software/dragen-decompression/orad.2.7.0.linux.tar.gz"
# FIXME - this is a temporary fix until we can get the arm64 binary
ARG ORAD_AARCH_64_DOWNLOAD_URL="https://media.githubusercontent.com/media/umccr/orcabus/refs/heads/main/lib/workload/components/ora-file-decompression-fq-pair-sfn/tasks/ora_decompression/binaries/orad.tar.gz"
ARG ORA_MOUNT="/opt"

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
  wget \
    --quiet \
    --output-document "awscliv2.zip" \
    "https://awscli.amazonaws.com/awscli-exe-linux-${platform_url}.zip" && \
  unzip -q "awscliv2.zip" && \
  ./aws/install && \
  rm "awscliv2.zip"

# Install ORA
# Install the ora reference data directly into the docker container
# Remove the orad x86-64 binary since we use the arm64 binary provided instead
RUN \
    mkdir --parents --mode 744 "${ORA_MOUNT}" && \
    wget --quiet \
     --output-document /dev/stdout \
     "${ORAD_REF_DOWNLOAD_URL}" | \
    tar \
       --directory "${ORA_MOUNT}" \
       --extract \
       --gunzip \
       --strip-components=1 \
       --file - && \
    chmod 644 "${ORA_MOUNT}/oradata/" && \
    chmod a+x "${ORA_MOUNT}/orad" && \
    rm "${ORA_MOUNT}/orad"

# Set the ora reference to the path ORA_MOUNT/oradata
ENV ORADATA_PATH="${ORA_MOUNT}/oradata/"

# Add the orad binary to the docker container
# And make it executable
RUN \
    wget \
      --quiet \
      --output-document /dev/stdout \
      "${ORAD_AARCH_64_DOWNLOAD_URL}" | \
    tar \
      --directory /usr/local/bin \
      --extract \
      --gzip \
      --file - && \
    chmod +x /usr/local/bin/orad
