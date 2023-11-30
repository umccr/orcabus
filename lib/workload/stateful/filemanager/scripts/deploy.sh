#!/bin/sh -x

export AWS_ENDPOINT_URL=http://localhost:4566
export FM_BUCKET=filemanager-test-ingest

docker compose down
docker compose up --wait --wait-timeout 20 -d
cd deploy
npm install
yes | npx cdklocal destroy
yes | npx cdklocal bootstrap
cd ../database && sqlx migrate run && cd ..

cd deploy && yes | npx cdklocal deploy --require-approval never && cd ..

aws s3 mb s3://$FM_BUCKET
aws s3api put-object --bucket $FM_BUCKET --key test
