ARG EDGEDB_VERSION

FROM edgedb/edgedb:${EDGEDB_VERSION}

# Copy dbschema which contain the migrations to the image
# Migrations will automatically applied
# Ref: https://www.edgedb.com/docs/guides/deployment/docker#schema-migrations
COPY dbschema/ ./dbschema/
