#!/bin/sh

cargo watch --watch-when-idle -w *.toml -w *.rs -- ./scripts/deploy.sh
