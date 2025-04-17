FROM public.ecr.aws/lambda/python:3.12

ARG TARGETPLATFORM
ARG NTSM_VERSION="1.2.1"
ARG NTSM_DOWNLOAD_URL="https://github.com/JustinChu/ntsm/releases/download/${NTSM_VERSION}/ntsm-${NTSM_VERSION}.tar.gz"

ARG APP_ROOT=./

RUN \
  dnf update -y && \
  dnf install -y \
    tar \
    wget \
    gzip \
    make \
    gcc \
    g++ \
    zlib-devel \
    && \
  ( \
    wget "${NTSM_DOWNLOAD_URL}" && \
    tar -xzf "$(basename "${NTSM_DOWNLOAD_URL}")" && \
    cd "$(basename "${NTSM_DOWNLOAD_URL}" .tar.gz)" && \
    ./configure && \
    make && \
    make install \
  ) && \
  pip install --break-system-packages pandas


# Copy the lambda contents
COPY ${APP_ROOT}/ntsm_eval.py ./

CMD ["ntsm_eval.handler"]