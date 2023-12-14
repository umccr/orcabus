#!/bin/sh -x
# TODO: Takes too long for re-deploy, find further shortcuts

export FM_BUCKET=filemanager-test-ingest

docker compose down
docker compose up --wait --wait-timeout 20 -d

cd deploy || exit
npm install
yes | npx cdklocal destroy
yes | npx cdklocal bootstrap

cd ../database && sqlx migrate run && cd ..

cd deploy && yes | npx cdklocal deploy --require-approval never && cd ..

aws s3api put-object --bucket $FM_BUCKET --key test
