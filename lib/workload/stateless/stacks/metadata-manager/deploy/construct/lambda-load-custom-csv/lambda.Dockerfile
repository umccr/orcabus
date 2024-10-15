FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# COPY all files
COPY . .

# Install the specified packages
RUN pip install -r deps/requirements-full.txt

# Specify handler
CMD [ "handler.load_custom_metadata_csv.handler" ]
