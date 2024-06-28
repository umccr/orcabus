# Taken from https://github.com/badouralix/rclone-lambda-sync/blob/main/lambda_function.py

import asyncio
import json
import logging
import os
import tomli_w
from pathlib import Path

import boto3
from pythonjsonlogger import jsonlogger

from lambda_types import LambdaContext, LambdaDict

# We won't use the root logger, but rather a dedicated logger for this __name__
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def handler(event: LambdaDict, context: LambdaContext) -> LambdaDict:
    """
    lambda_handler is the default entrypoint of the lambda.
    """
    update_root_logger()
    asyncio.run(run_rclone_sync(event))

    return dict()


def update_root_logger() -> None:
    """
    update_root_logger overwrites the root logger with a custom json formatter.

    Datadog might patch the root handler formatter at each execution, and we have to overwrite it at each run
    https://github.com/DataDog/datadog-lambda-python/blob/afbbef5/datadog_lambda/tracing.py#L304-L327
    """
    # Craft a dedicated json formatter for the lambda logs
    # We add all available attributes along with the aws request id
    #
    # https://github.com/python/cpython/blob/ea39f82/Lib/logging/__init__.py#L539-L562
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    # https://docs.datadoghq.com/logs/log_collection/python/?tab=pythonjsonlogger
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(created)f %(filename)s %(funcName)s %(levelname)s %(levelno)s %(lineno)d %(message)s %(module)s %(msecs)d %(name)s %(pathname)s %(process)d %(processName)s %(relativeCreated)d %(thread)d %(threadName)s"
        + "%(aws_request_id)s",
        rename_fields={
            "aws_request_id": "lambda.request_id"
        },  # Remap field to match datadog conventions
        reserved_attrs=jsonlogger.RESERVED_ATTRS
        + (
            "dd.env",
            "dd.service",
            "dd.version",
        ),  # For some reason these tags end up empty, so better exclude them by setting them as reserved attributes
    )

    # We need to change the formatter of the handler of the root logger, since all logs are propagated upwards in the tree
    # In particular, the root logger already has a handler provider by aws lambda bootstrap.py
    #
    # https://docs.python.org/3/library/logging.html#logging.Logger.propagate
    # https://stackoverflow.com/a/50910673
    # https://stackoverflow.com/questions/37703609/using-python-logging-with-aws-lambda
    # https://www.denialof.services/lambda/
    root = logging.getLogger()
    for handler in root.handlers:
        if handler.__class__.__name__ == "LambdaLoggerHandler":
            handler.setFormatter(formatter)


async def run_rclone_sync(event: LambdaDict) -> None:
    """
    run_rclone_sync is the main function spawning an rclone process and parsing its output.
    """
    logger.info("Starting rclone sync")
    config_fname = generate_rclone_config(
        Path("/tmp/rclone.conf")
    )
    source = (
        str(event.get("RCLONE_SYNC_CONTENT_SOURCE", ""))
        or os.environ.get("RCLONE_SYNC_CONTENT_SOURCE")
        or "source:/"
    )
    destination = (
        str(event.get("RCLONE_SYNC_CONTENT_DESTINATION", ""))
        or os.environ.get("RCLONE_SYNC_CONTENT_DESTINATION")
        or "destination:/"
    )
    cmd = [
        "rclone",
        "--config",
        config_fname,
        "--use-json-log",
        "--verbose",
        "sync",
        "--stats",
        "10s",
        source,
        destination,
        *os.environ.get("RCLONE_SYNC_EXTRA_FLAGS", "").split(),
    ]
    if os.environ.get("RCLONE_SYNC_DRY_RUN", "false") != "false":
        cmd.append("--dry-run")
    logger.info(f"Running command {cmd}")
    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # We need to consume both stdout and stderr to avoid blocking the subprocess
    #
    # https://stackoverflow.com/a/61939464
    await asyncio.gather(p.wait(), log_stdout(p.stdout), log_stderr(p.stderr))
    logger.info("Finished rclone sync")

def generate_rclone_config(conf_path: Path):
    """
    get_rclone_config_path retrieves rclone config from AWS SSM and dumps it on a temp file.
    """

    ssm = boto3.client("ssm")

    rclone_config = {
        "src": {
            "type": "s3",
            "provider": "AWS",
            "access_key_id": ssm.get_parameter(Name='icav1_aws_access_key_id')['Parameter'].get('Value', 'NotFound'),
            "secret_access_key": ssm.get_parameter(Name='icav1_aws_secret_access_key')['Parameter'].get('Value', 'NotFound'),
            "session_token": ssm.get_parameter(Name='icav1_aws_session_token')['Parameter'].get('Value', 'NotFound'),
            "region": os.environ.get('AWS_REGION', 'AWS_DEFAULT_REGION')
        },
        "dest": {
            "type": "s3",
            "provider": "AWS",
            "access_key_id": os.environ.get('AWS_ACCESS_KEY_ID'),
            "secret_access_key": os.environ.get('AWS_SECRET_ACCESS_KEY'),
            "session_token": os.environ.get('AWS_SESSION_TOKEN'),
            "region": os.environ.get('AWS_REGION', 'AWS_DEFAULT_REGION')
        }
    }

    # Write configuration file
    with open(conf_path, 'wb') as config:
        tomli_w.dump(rclone_config, config)

    # Fix the quotes
    with open(conf_path, 'r+') as no_quotes:
        to_clean = no_quotes.read()
        clean = to_clean.replace('"', '')
        no_quotes.seek(0)
        no_quotes.write(clean)
        no_quotes.truncate()
        no_quotes.close()
        return no_quotes.name

async def log_stdout(stream: asyncio.StreamReader | None) -> None:
    """
    log_stdout consumes rclone stdout line by line and generates python logs out of it.
    """
    if stream is None:
        logger.error("Invalid stream in log_stdout")
        return
    while line := await stream.readline():
        try:
            log_rclone(line)
        except json.JSONDecodeError as _:
            logger.info(line.decode())


async def log_stderr(stream: asyncio.StreamReader | None) -> None:
    """
    log_stderr consumes rclone stderr line by line and generates python logs out of it.
    """
    if stream is None:
        logger.error("Invalid stream in log_stderr")
        return
    while line := await stream.readline():
        try:
            log_rclone(line)
        except json.JSONDecodeError as _:
            logger.error(line.decode())


def log_rclone(line: bytes) -> None:
    """
    log_rclone parses and reshapes rclone json logs.
    """
    d = {"rclone": json.loads(line)}

    # Remap message key
    d["message"] = d["rclone"].pop("msg")

    # Notice logs become warning logs in logrus
    # Remap log level accordingly
    if "stats" in d["rclone"]:
        d["level"] = "debug"
    elif "skipped" in d["rclone"]:
        d["level"] = "info"
    else:
        d["level"] = d["rclone"]["level"]
    d["rclone"].pop("level")

    # The log level does not really matter here, since rclone already specifies its own log level
    logger.error(d)