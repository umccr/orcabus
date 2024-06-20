import logging
from unittest import skip

from django.db.models import Q
from django.test import TestCase

from workflow_manager.models.base import OrcaBusBaseManager, OrcaBusBaseModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class OrcaBusBaseManagerTestCase(TestCase):

    def setUp(self) -> None:
        pass

    @skip
    def test_reduce_multi_values_qor(self):
        """
        python manage.py test workflow_manager.tests.test_base.OrcaBusBaseManagerTestCase.test_reduce_multi_values_qor
        """
        q = OrcaBusBaseManager.reduce_multi_values_qor('subject_id', ["SBJ000001", "SBJ000002"])
        logger.info(q)
        self.assertIsNotNone(q)
        self.assertIsInstance(q, Q)
        self.assertIn(Q.OR, str(q))

    @skip
    def test_reduce_multi_values_qor_auto_pack(self):
        """
        python manage.py test workflow_manager.tests.test_base.OrcaBusBaseManagerTestCase.test_reduce_multi_values_qor_auto_pack
        """
        q = OrcaBusBaseManager.reduce_multi_values_qor('subject_id', "SBJ000001")
        logger.info(q)
        self.assertIsNotNone(q)
        self.assertIsInstance(q, Q)
        self.assertIn(Q.AND, str(q))

    @skip
    def test_base_model_must_abstract(self):
        """
        python manage.py test workflow_manager.tests.test_base.OrcaBusBaseManagerTestCase.test_base_model_must_abstract
        """
        try:
            OrcaBusBaseModel()
        except TypeError as e:
            logger.exception(f"THIS ERROR EXCEPTION IS INTENTIONAL FOR TEST. NOT ACTUAL ERROR. \n{e}")
        self.assertRaises(TypeError)
