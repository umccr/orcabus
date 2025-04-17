__ORA_IMAGE_HEADER__

ARG SEQUALI_VERSION="0.11.1"

# ADDITION: Install uv / uvx
RUN apt update -y -q && \
    apt install -y -q python3 curl && \
    curl -LsSf https://astral.sh/uv/install.sh | XDG_CONFIG_HOME=/tmp UV_INSTALL_DIR=/usr/bin sh

# Install sequali with uvx
RUN uvx pip install sequali=="${SEQUALI_VERSION}"

# Copy the docker entrypoint to the docker container
COPY docker-entrypoint.sh docker-entrypoint.sh
COPY summarise_stats.py summarise_stats.py

# Make the docker entrypoint executable
RUN chmod +x "./docker-entrypoint.sh"
RUN chmod +x "./summarise_stats.py"

# Set the entrypoint as the docker entrypoint script
CMD [ "./docker-entrypoint.sh" ]
