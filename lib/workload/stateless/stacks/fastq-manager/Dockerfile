FROM python:3.12

ARG PORT=8457

WORKDIR /code

COPY ./app /code/app

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt

ENV PORT=$PORT

EXPOSE $PORT

CMD exec fastapi run app/handler.py --port "${PORT}"