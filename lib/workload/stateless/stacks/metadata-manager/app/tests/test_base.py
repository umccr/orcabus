import logging

from django.db.models import Q
from django.test import TestCase

from app.models.base import BaseManager, BaseModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class BaseManagerTestCase(TestCase):
    def setUp(self) -> None:
        pass

    def test_reduce_multi_values_qor(self):
        """
        python manage.py tests app.tests.test_base.BaseManagerTestCase.test_reduce_multi_values_qor
        """
        q = BaseManager.reduce_multi_values_qor(
            "subject_id", ["SBJ000001", "SBJ000002"]
        )
        logger.info(q)
        self.assertIsNotNone(q)
        self.assertIsInstance(q, Q)
        self.assertIn(Q.OR, str(q))

    def test_reduce_multi_values_qor_auto_pack(self):
        """
        python manage.py tests app.tests.test_base.BaseManagerTestCase.test_reduce_multi_values_qor_auto_pack
        """
        q = BaseManager.reduce_multi_values_qor("subject_id", "SBJ000001")
        logger.info(q)
        self.assertIsNotNone(q)
        self.assertIsInstance(q, Q)
        self.assertIn(Q.AND, str(q))

    def test_base_model_must_abstract(self):
        """
        python manage.py tests app.tests.test_base.BaseManagerTestCase.test_base_model_must_abstract
        """
        try:
            BaseModel()
        except TypeError as e:
            logger.exception(
                f"THIS ERROR EXCEPTION IS INTENTIONAL FOR TEST. NOT ACTUAL ERROR. \n{e}"
            )
        self.assertRaises(TypeError)
