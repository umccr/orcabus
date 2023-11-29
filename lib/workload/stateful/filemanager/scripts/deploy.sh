#!/bin/sh -x

export AWS_ENDPOINT_URL=http://localhost:4566
export FM_BUCKET=filemanager-test-ingest

cd deploy
yes | npx cdklocal destroy
yes | npx cdklocal bootstrap
yes | npx cdklocal deploy --require-approval never
cd ../database && sqlx migrate run && cd ..

aws s3 mb s3://$FM_BUCKET 
aws s3api put-object --bucket $FM_BUCKET --key test

./scripts/logs.sh
