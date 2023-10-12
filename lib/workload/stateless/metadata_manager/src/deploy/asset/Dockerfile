FROM public.ecr.aws/lambda/nodejs:18 as app-builder

FROM edgedb/edgedb AS edgedb-builder

# bring in the compatible node binary
COPY --from=node-deps /usr/local/bin/node /usr/local/bin/node

# setup a /build that edgedb can work in
RUN mkdir /build && chown edgedb:edgedb /build
USER edgedb
WORKDIR /build

# bring in node_modules with our installed packages
COPY --from=node-deps ../../src .

# edgedb needs the dbschema folder which has the schemas/migrations/queries
COPY --chown=edgedb ../../dbschema dbschema/

WORKDIR /a

# we use a matching CLI binary from our builder - and keep it for some admin level activity (migrations etc)
# NOTE this is a path that is just referred to in some of the entrypoint - so this is just expected to exist for
# some things to function
# TODO add a startup check the make sure it does exist
COPY --from=edgedb-builder /usr/bin/edgedb /a/

# bring in needed configs and migrations
# NOTE these need to be relative to the current directory of where node launches from (not relative to entrypoint src)
COPY --from=edgedb-builder /build/dbschema/migrations/ /a/dbschema/migrations/
COPY --from=app-builder /build/backend/config/ /a/config/
COPY --from=app-builder /build/backend/locales/ /a/locales/
COPY --from=app-builder /build/backend/emails/ /a/emails/

# bring in any node_modules incompatible with bundling (including dependencies of these modules too)
COPY --from=app-builder /build/backend/node_modules/node-gyp-build/ /a/node_modules/node-gyp-build/
COPY --from=app-builder /build/backend/node_modules/sodium-native/ /a/node_modules/sodium-native/
COPY --from=app-builder /build/backend/node_modules/jsonpath/ /a/node_modules/jsonpath/
# these are recursive dependencies of jsonpath - that itself can't be bundled
COPY --from=app-builder /build/backend/node_modules/static-eval/ /a/node_modules/static-eval/
COPY --from=app-builder /build/backend/node_modules/escodegen/ /a/node_modules/escodegen/
COPY --from=app-builder /build/backend/node_modules/esutils/ /a/node_modules/esutils/
COPY --from=app-builder /build/backend/node_modules/esprima/ /a/node_modules/esprima/
COPY --from=app-builder /build/backend/node_modules/underscore/ /a/node_modules/underscore/


CMD ["src/handler/migrate.handler"]