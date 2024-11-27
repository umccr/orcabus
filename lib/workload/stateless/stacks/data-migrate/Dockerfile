FROM public.ecr.aws/docker/library/python:3.13

RUN apt update -y && apt install -y awscli && pip3 install poetry

WORKDIR /app

COPY . .
RUN poetry install --no-interaction --no-root

ENTRYPOINT ["poetry", "run", "dm"]
