import json
import logging
import os
import tempfile
import uuid
from types import SimpleNamespace

from libumccr.aws import libsm

from pg_dd.pg_dd import PgDDS3, PgDDLocal

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
    out_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))

    PgDDLocal(logger=logger, out_dir=out_dir).write_to_dir()
    PgDDS3(logger=logger, out_dir=out_dir).write_to_bucket()
