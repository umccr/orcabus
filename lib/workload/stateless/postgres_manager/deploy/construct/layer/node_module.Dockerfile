# This image will generate the node_modules needed for lambda and let
# the layer reference the output from this image

FROM public.ecr.aws/docker/library/node:20-alpine

WORKDIR /home/node/app

COPY package.json package.json
COPY yarn.lock yarn.lock
RUN yarn install --immutable

# making nodejs folder where as guided in the AWS lambda layer docs
RUN mkdir -p output/nodejs

# copy node_modules to that folder
RUN cp -r node_modules output/nodejs
