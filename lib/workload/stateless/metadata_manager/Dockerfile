FROM node:20
WORKDIR /app

COPY Makefile package.json yarn.lock tsconfig.json jest.config.js ./
COPY src/ ./src/
COPY tests/ ./tests/

COPY dbschema/queries ./dbschema/queries
COPY dbschema/migrations ./dbschema/migrations
COPY dbschema/*.esdl ./dbschema/

RUN make install
RUN make edgetypes

ENTRYPOINT [ "cross-env" "EDGEDB_HOST=edgedb" "yarn" "start" ]
