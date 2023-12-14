#!/bin/sh

cargo watch -w *.toml -w *.rs -- ./scripts/deploy.sh
