# NOTES -
# THIS IS FROM https://github.com/aws/aws-cdk/blob/main/packages/%40aws-cdk/aws-lambda-python-alpha/lib/Dockerfile
# We have made the following changes:
# 1. Added the installation of 'uv'
# 2. Addded in the UV_CACHE_DIR environment variable
# 3. Replaced 'pip' with 'uv pip' in the main code chunk
# 4. Replaced /usr/app/venv/pip with uv pip shell script wrapper
# The correct AWS SAM build image based on the runtime of the function will be
# passed as build arg. The default allows to do `docker build .` when testing.
ARG IMAGE=public.ecr.aws/sam/build-python3.12:latest
FROM $IMAGE

ARG TARGETPLATFORM
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG HTTPS_PROXY
ARG POETRY_VERSION=1.5.1

# ADDITION: Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | XDG_CONFIG_HOME=/tmp UV_INSTALL_DIR=/usr/bin sh

# Add virtualenv path
ENV PATH="/usr/app/venv/bin:$PATH"

# set the pip cache location
ENV PIP_CACHE_DIR=/tmp/pip-cache

# set the poetry cache
ENV POETRY_CACHE_DIR=/tmp/poetry-cache

# ADDITION: set the uv cache
ENV UV_CACHE_DIR=/tmp/uv-cache

# ADDITION: Replace 'pip' with uv pip in the following chunk
RUN \
    # create a new virtualenv for python to use
    # so that it isn't using root
    python -m venv /usr/app/venv && \
    # Create a new location for the pip cache
    mkdir /tmp/pip-cache && \
    # Ensure all users can write to pip cache
    chmod -R 777 /tmp/pip-cache && \
    # Upgrade pip (required by cryptography v3.4 and above, which is a dependency of poetry)
    uv pip install --upgrade pip && \
    # Create a new location for the poetry cache
    mkdir /tmp/poetry-cache && \
    # Ensure all users can write to poetry cache
    chmod -R 777 /tmp/poetry-cache && \
    # Ensure all users can write to uv cache
    chmod -R 777 /tmp/uv-cache && \
    # Install pipenv and poetry
    uv pip install poetry==$POETRY_VERSION && \
    # Ensure no temporary files remain in the caches
    rm -rf /tmp/pip-cache/* /tmp/poetry-cache/* /tmp/uv-cache/*

# ADDITION: Replace /usr/app/venv/pip with uv pip
RUN printf '#!/usr/bin/env bash \nuv pip $@\n' > /usr/app/venv/bin/pip && \
    printf '#!/usr/bin/env bash \nuv pip $@\n' > /usr/app/venv/bin/pip3

CMD [ "python" ]