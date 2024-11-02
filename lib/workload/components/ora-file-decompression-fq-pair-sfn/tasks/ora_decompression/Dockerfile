FROM --platform=${TARGETPLATFORM} ubuntu:noble

ARG ORAD_REF_DOWNLOAD_URL="https://s3.amazonaws.com/webdata.illumina.com/downloads/software/dragen-decompression/orad.2.7.0.linux.tar.gz"
ARG ORA_MOUNT="/opt"
ARG TARGETPLATFORM

# Install ubuntu basics
RUN \
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

## Install qemu-virtualization
## Commented out as we now have an orad arm64 binary version
## Add amd64 sources
#RUN \
#  apt install -yq \
#    qemu-user-static \
#    binfmt-support && \
#  echo "Adding multi-arch package sources" 1>2 && \
#  rm "/etc/apt/sources.list.d/ubuntu.sources" && \
#  echo 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ noble main restricted universe multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ noble-updates main restricted universe multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ noble-security main restricted universe multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ noble-backports main restricted universe multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ noble main universe restricted multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ noble-updates main universe restricted multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ noble-backports main universe restricted multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  echo 'deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ noble-security main universe restricted multiverse' >> '/etc/apt/sources.list.d/ubuntu.list' && \
#  dpkg --add-architecture amd64 && \
#  apt update -yq && \
#  apt install -yq \
#    libc6:amd64 \
#    uuid-dev:amd64

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
ADD binaries/orad.tar.gz /usr/local/bin/
RUN chmod +x /usr/local/bin/orad

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

