FROM public.ecr.aws/docker/library/python:3.12

WORKDIR /app

COPY . .

RUN make install

ENTRYPOINT ["make", "start"]
