FROM --platform=${TARGETPLATFORM} public.ecr.aws/lambda/python:3.12

LABEL maintainer="Alexis Lucattini"

# Build args
ARG APP_ROOT=.

# Copy over the requirements
COPY ${APP_ROOT}/requirements.txt ./

# Install htslib
RUN \
    dnf update -y && \
    dnf install -y \
      gzip \
      wget && \
    echo "Install awsv2 cli" 1>&2 && \
    pip install --upgrade \
      awscli && \
    echo "Install sequali" 1>&2 && \
    pip install -r requirements.txt

# Copy the lambda contents
COPY ${APP_ROOT}/get_sequali_stats.py ./

CMD ["get_sequali_stats.handler"]
