FROM amazon/aws-lambda-python:3.12

LABEL maintainer="Alexis Lucattini"

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
      xz-devel && \
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
    pip install \
      wrapica \
      bgzip

CMD ["compress_icav2_vcf.lambda_handler"]
