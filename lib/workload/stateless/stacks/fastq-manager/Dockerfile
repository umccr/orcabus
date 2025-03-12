FROM python:3.12

ARG PORT=8457

WORKDIR /code

# ADDITION: Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | XDG_CONFIG_HOME=/tmp UV_INSTALL_DIR=/usr/bin sh

COPY ./docker/metadata_tools_layer /code/metadata_tools_layer
COPY ./docker/filemanager_tools_layer /code/filemanager_tools_layer

RUN uv pip install --system --no-cache-dir --upgrade /code/metadata_tools_layer/
RUN uv pip install --system --no-cache-dir --upgrade /code/filemanager_tools_layer/

COPY ./app/api /code/api
RUN uv pip install --system --no-cache-dir --upgrade -r /code/api/requirements.txt

ENV PORT=$PORT

EXPOSE $PORT

CMD exec fastapi run api/handler.py --port "${PORT}"
