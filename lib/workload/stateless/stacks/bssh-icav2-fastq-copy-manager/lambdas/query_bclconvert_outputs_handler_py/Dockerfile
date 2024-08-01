FROM public.ecr.aws/lambda/python:3.12

LABEL maintainer="Alexis Lucattini"

# Attempting logic from https://stackoverflow.com/a/68071471/6946787
# Context is in directory above
ARG APP_ROOT=.
ARG THIS_DIR_NAME="lambdas/query_bclconvert_outputs_handler_py"

RUN dnf update -y && \
    pip install --upgrade pip

# Copy over required files
COPY ${APP_ROOT}/${THIS_DIR_NAME}/ ./
COPY ${APP_ROOT}/layers/ ./layers/

RUN ( \
      chmod +rx ./query_bclconvert_outputs_handler.py && \
      cd layers && \
      python3 -m pip install . \
    )

CMD ["query_bclconvert_outputs_handler.lambda_handler"]
