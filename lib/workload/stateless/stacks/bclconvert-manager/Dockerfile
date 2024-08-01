FROM public.ecr.aws/lambda/python:3.12

LABEL maintainer="Alexis Lucattini"

# Attempting logic from https://stackoverflow.com/a/68071471/6946787
# Context is in directory above
ARG APP_ROOT=.
ARG THIS_DIR_NAME="translator_service"

RUN dnf update -y && \
    pip install --upgrade pip

# Copy over required files
COPY ${APP_ROOT}/${THIS_DIR_NAME}/ ./
COPY ${APP_ROOT}/deps/ ./layers/

RUN ( \
      chmod +rx ./icav2_event_translator.py && \
      cd layers && \
      python3 -m pip install -r requirements.txt \
    )

CMD ["icav2_event_translator.lambda_handler"]