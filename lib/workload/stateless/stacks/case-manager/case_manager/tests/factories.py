import json
from enum import Enum
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
import factory
from django.utils.timezone import make_aware

from case_manager.models import Case, CaseData, Library, State


class TestConstant(Enum):
    case_name = "TestCase1"
    case_data = {
        "key": "value",
        "foo": uuid.uuid4(),
        "bar": datetime.now().astimezone(ZoneInfo('Australia/Sydney')),
        "sub": {"my": "sub"}
    },
    library = {
        "library_id": "L000001",
        "orcabus_id": "01J5M2J44HFJ9424G7074NKTGN"
    }


class CaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Case

    cref = "Curation Test case 1"
    name = "Test Case"
    type = "WGTS"
    description = "A test case created for testing ;-)"

    compute_env = "research"
    data_env = "research"


class CaseDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CaseData

    data = TestConstant.case_data.value
    case = None  # If required, set later


class LibraryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Library

    library_id = TestConstant.library.value["library_id"]
    orcabus_id = TestConstant.library.value["orcabus_id"]


class StateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = State

    status = "READY"
    timestamp = make_aware(datetime.now())
    comment = "Comment"
    case = factory.SubFactory(CaseFactory)
