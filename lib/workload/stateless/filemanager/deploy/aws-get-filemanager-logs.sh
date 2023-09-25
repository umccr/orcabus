#!/bin/bash

function usage() {
  usage="$(basename "$0") [-h] [-c awslocal|aws] -- get cloudwatch logs from the filemanager lambda functions

  commands:
    awslocal  use awslocal
    aws  use regular aws cli

  options:
      -h  show this help text
      -c  the command for this script to run [default: not set, required]"

  echo "$usage"
}

function run_command() {
  group_name=$("$command" logs describe-log-groups --query logGroups[*].logGroupName | jq -r '.[]')
  "$command" logs tail "$group_name" --follow
}

command=""
while getopts ':hc:' option; do
  case "$option" in
    h)
      usage
      exit
      ;;
    c)
      command="$OPTARG"
      ;;
    :)
      printf "missing argument for -%s\n" "$OPTARG" >&2
      usage >&2
      exit 1
      ;;
    \?)
      printf "invalid option: -%s\n" "$OPTARG" >&2
      usage >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND - 1))

if [[ -z "$command" ]]; then
  printf "command option must be set\n" >&2
  usage >&2
  exit 1
fi

run_command