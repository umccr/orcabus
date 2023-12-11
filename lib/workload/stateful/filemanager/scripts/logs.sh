#!/bin/sh -x

export AWS_ENDPOINT_URL=http://localhost:4566

# Don't die when the whole stack re-deploys
group_name=$(aws logs describe-log-groups --query 'logGroups[*].logGroupName' --output text)
aws logs tail "$group_name" --follow
