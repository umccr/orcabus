FROM alpine:latest as layer-copy

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_SESSION_TOKEN
ENV AWS_DEFAULT_REGION="ap-southeast-2"
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ENV AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN

RUN apk add aws-cli curl unzip
RUN mkdir -p /opt

# Getting AWS managed lambda layer injected in the image
# We are using the extension for access secrets and parameter
# Ref: Ref: https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html
RUN curl $(aws lambda get-layer-version-by-arn --arn arn:aws:lambda:ap-southeast-2:665172237481:layer:AWS-Parameters-and-Secrets-Lambda-Extension-Arm64:11 --query 'Content.Location' --output text) --output layer.zip
RUN unzip layer.zip -d /opt
RUN rm layer.zip

FROM public.ecr.aws/lambda/nodejs:20-arm64 as builder
WORKDIR /usr/app

# Copying existing required file to the image
# `make edgetypes` that is for querying edgedb must exist before this
COPY package.json yarn.lock tsconfig.json jest.config.js ./
COPY dbschema/ ./dbschema/
COPY src/ ./src/
COPY tests/ ./tests/

# Building necessary file for the lambda
RUN npm install -g yarn
RUN yarn -v
RUN yarn install
RUN yarn run build-src

FROM public.ecr.aws/lambda/nodejs:20-arm64

# Copy the extensions here
WORKDIR /opt
COPY --from=layer-copy  /opt/ .

# Copy the rest of the code
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /usr/app/dist/ ./
COPY --from=builder /usr/app/node_modules/ ./node_modules/
