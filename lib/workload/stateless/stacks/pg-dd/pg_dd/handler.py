import json
import logging
import os
from types import SimpleNamespace

from libumccr.aws import libsm

from pg_dd.pg_dd import PgDDS3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    secret_str = libsm.get_secret(os.getenv("PG_DD_SECRET"))
    secret = json.loads(secret_str, object_hook=lambda d: SimpleNamespace(**d))
    os.environ["PG_DD_URL"] = (
        f"{secret.engine}://{secret.username}:{secret.password}@{secret.host}:{secret.port}"
    )
except Exception as e:
    logger.error(f"retrieving database url from secrets manager: {e}")
    raise e


def handler(_event, _context):
    PgDDS3(logger=logger).write_to_bucket()
