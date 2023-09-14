#!/bin/bash

find ./migrations -type f -print0 | while IFS= read -r -d $'\0' file; do
    echo "Running migration for $file"
    psql "$@" -d filemanager -a -f "$file"
done