FROM python:3.12

WORKDIR /code

COPY ./app /code/app

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt

CMD ["fastapi", "run", "app/main.py", "--port", "8001"]