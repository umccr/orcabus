#!/bin/bash

LAYER_NAME=$1
SCRIPT_DIR=$(dirname $0)
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

if test -z "$LAYER_NAME"; then
    echo "LAYER_NAME is not set! Specify the layer for which to create the Lambda package."
    exit 1
fi

# spcifiy the lib directory (according to AWS Lambda guidelines)
export PKG_DIR=$SCRIPT_DIR/"python"
export LAYER_DIR=$SCRIPT_DIR/${LAYER_NAME}

# clean up any existing files
rm -rf ${PKG_DIR} && mkdir -p ${PKG_DIR}
cp -R ${LAYER_DIR}/ ${PKG_DIR}/

# install the python libraries (without dependencies)
docker run \
  --platform=linux/x86-64 \
  --rm \
  -v ${SCRIPT_PATH}/python:/foo \
  -w /foo \
  public.ecr.aws/sam/build-python3.9 \
  pip install -r requirements.txt --no-deps -t ./

# clean the lib directory
rm -rf ${PKG_DIR}/*.dist-info
find python -type d -name __pycache__ -exec rm -rf {} +

# create the package zip
zip -r ${LAYER_DIR}.zip ${PKG_DIR}/

# remove the inflated directory
rm -rf ${PKG_DIR}/
