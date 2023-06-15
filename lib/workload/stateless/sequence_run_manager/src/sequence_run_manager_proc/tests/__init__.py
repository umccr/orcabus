import string
import random
import uuid


def _rand(length=8):
    alpha_numeric = string.ascii_letters + string.digits
    return "".join((random.choice(alpha_numeric) for i in range(length)))


def _uuid():
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, "umccr.org"))
