FROM --platform=${TARGETPLATFORM} public.ecr.aws/lambda/python:3.12

LABEL maintainer="Alexis Lucattini"

# Build args
ARG APP_ROOT=.
ARG FASTQC_GIT_COMMIT="1faeea0"
ARG FASTQC_VERSION="0.12.1-dev"
ARG FASTQC_GITHUB_URL="https://github.com/s-andrews/FastQC"

# Copy over the requirements
COPY ${APP_ROOT}/requirements.txt ./

# Install htslib
RUN \
    dnf update -y && \
    dnf install -y \
      git \
      wget \
      java \
      java-devel \
      ant \
      perl && \
    echo "Install fastqc" 1>&2 && \
    mkdir /opt/fastqc/ && \
    ( \
        cd /opt/fastqc/ && \
        git clone \
            "${FASTQC_GITHUB_URL}" \
            "${FASTQC_VERSION}" && \
        cd "${FASTQC_VERSION}" && \
        git checkout "${FASTQC_GIT_COMMIT}" && \
        JAVA_HOME="/usr/lib/jvm/java/" ant && \
        chmod +x "bin/fastqc" && \
        ln -s "$PWD/bin/fastqc" "/usr/local/bin/fastqc" \
    ) && \
    echo "Install awsv2 cli" 1>&2 && \
    pip install --upgrade \
      awscli && \
    pip install -r requirements.txt

# Copy the lambda contents
COPY ${APP_ROOT}/run_fastqc.py ./

CMD ["run_fastqc.handler"]
