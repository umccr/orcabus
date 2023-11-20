npx cdklocal bootstrap
npx cdklocal deploy

awslocal s3api put-object --bucket filemanager-test-ingest --key test

/bin/bash aws-get-filemanager-logs.sh -c awslocal > logs.txt