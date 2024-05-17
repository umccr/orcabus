# coding: utf-8

from __future__ import absolute_import

from .marshaller import Marshaller
from .AWSEvent import AWSEvent
from .Payload import Payload
from .WorkflowRunStateChange import WorkflowRunStateChange

from datetime import datetime, timezone
from uuid import uuid4
import hashlib


def generate_portal_run_id() -> str:
    # Initialise hashlib
    h = hashlib.new('sha256')

    # Update with uuid4
    h.update(str(uuid4()).encode())
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d')}{h.hexdigest()[:8]}"
