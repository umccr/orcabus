#!/bin/bash

args=()

if [ -z "$1" ]
  then
    echo "No user supplied, using default"
  else
    args+=( "-u" )
    args+=( "$1" )
fi

find ./migrations -type f -print0 | while IFS= read -r -d $'\0' file; do
    echo "Running migration for $file"
    psql "${args[@]}" -d filemanager -a -f "$file"
done