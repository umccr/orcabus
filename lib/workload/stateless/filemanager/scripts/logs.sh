#!/bin/sh -x

# Don't die when the whole stack re-deploys
group_name=$(aws logs describe-log-groups --query 'logGroups[*].logGroupName' --output text)
aws logs tail "$group_name" --follow
