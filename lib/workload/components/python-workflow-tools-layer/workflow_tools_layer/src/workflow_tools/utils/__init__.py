#!/usr/bin/env python3

import re


def strip_context_from_orcabus_id(orcabus_id: str) -> str:
    """
    Strip the context from the orcabus_id
    :param orcabus_id:
    :return:
    """
    return re.sub(r"^(\w+).", "", orcabus_id)