FROM --platform=${TARGETPLATFORM} public.ecr.aws/lambda/python:3.12

LABEL maintainer="Alexis Lucattini"

# Build args
ARG APP_ROOT=.

# Code args
ARG HTSLIB_VERSION="1.20"

# Install htslib
RUN \
    dnf update -y && \
    dnf install -y \
      wget \
      gcc \
      make \
      tar \
      bzip2 \
      zlib-devel \
      bzip2-devel \
      xz-devel \
      openssl-devel \
      libcurl-devel && \
    wget --quiet --output-document "htslib-${HTSLIB_VERSION}.tar.bz2" \
      "https://github.com/samtools/htslib/releases/download/${HTSLIB_VERSION}/htslib-${HTSLIB_VERSION}.tar.bz2" && \
    tar -xf "htslib-${HTSLIB_VERSION}.tar.bz2" && \
    ( \
        cd "htslib-${HTSLIB_VERSION}" && \
          ./configure --prefix=/usr/ && \
        make && \
        make install \
    ) && \
    rm -rf "htslib-${HTSLIB_VERSION}" "htslib-${HTSLIB_VERSION}.tar.bz2" && \
    pip install --upgrade pip && \
    pip install \
      wrapica \
      bgzip

# Copy the lambda contents
COPY ${APP_ROOT}/compress_icav2_vcf.py ./

CMD ["compress_icav2_vcf.handler"]
