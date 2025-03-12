__ORA_IMAGE_HEADER__

LABEL maintainer="Alexis Lucattini"

# Copy the docker entrypoint to the docker container
COPY docker-entrypoint.sh docker-entrypoint.sh

# Make the docker entrypoint executable
RUN chmod +x "./docker-entrypoint.sh"

# Set the entrypoint as the docker entrypoint script
CMD [ "./docker-entrypoint.sh" ]

