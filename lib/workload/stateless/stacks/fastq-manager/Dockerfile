FROM python:3.12

ARG PORT=8457

WORKDIR /code

COPY ./app /code/app

COPY ./docker/metadata_tools_layer /code/metadata_tools_layer
COPY ./docker/filemanager_tools_layer /code/filemanager_tools_layer

RUN pip install --no-cache-dir --upgrade -r /code/app/requirements.txt
RUN pip install --no-cache-dir --upgrade /code/metadata_tools_layer/
RUN pip install --no-cache-dir --upgrade /code/filemanager_tools_layer/

ENV PORT=$PORT

EXPOSE $PORT

CMD exec fastapi run app/handler.py --port "${PORT}"
