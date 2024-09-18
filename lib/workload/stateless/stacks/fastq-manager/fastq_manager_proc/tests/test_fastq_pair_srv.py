from fastq_manager.tests.factories import FastqPairFactory
from fastq_manager.models.fastq_pair import FastqPair
from fastq_manager_proc.services import fastq_pair_srv
from fastq_manager_proc.tests.case import FastqPairProcUnitTestCase, logger


class FastqPairSrvUnitTests(FastqPairProcUnitTestCase):

    def test_get_fastq_pair_from_db(self):
        """
        python manage.py fastq_manager_proc.tests.test_fastq_pair_srv.FastqPairSrvUnitTests.test_get_fastq_pair_from_db
        """
        rgid = "test.id.123"
        FastqPairFactory(rgid=rgid)

        fp: FastqPair = fastq_pair_srv.get_fastq_pair_from_db(rgid=rgid)
        logger.info(fp)
        self.assertIsNotNone(fp)
        self.assertEqual(rgid, fp.rgid)
