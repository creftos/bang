import unittest
from moto import mock_sqs
from mock import MagicMock
import boto
from bang.sqslistener.sqslistener import SQSListener
from boto.sqs.message import Message
from bang.sqslistener.sqsmultiprocessutils import start_job_process
from bang.sqslistener.sqslistener import RequestMessage
import yaml
from bang.sqslistener.non_daemonized_pool import MyPool

LISTENER_CONFIG_PATH = 'tests/resources/sqslistener/.sqslistener'

test_request_message_body = ("---\n"
                             "test_job_1:\n"
                             "  request_id: test-job-id-for-sqs-bang-integration\n")

class SQSListenerBangIntegration(unittest.TestCase):

    def start_job_process_test(self):
        boto_sqs_patcher = mock_sqs()
        mockClass = boto_sqs_patcher.start()

        mock_connection = boto.connect_sqs()
        mock_connection.create_queue('bang-queue')
        mock_connection.create_queue('bang-response')

        boto.sqs.connect_to_region = MagicMock(name="mock_connect_to_sqs", return_value=mock_connection)

        sqslistener = SQSListener(listener_config_path=LISTENER_CONFIG_PATH)

        message = Message(body=test_request_message_body)

        job = sqslistener.job_set.generate_job("test_job_1", None)

        request_message = RequestMessage(message)

        pool = MyPool(processes=10)

        completed_message_body = \
            start_job_process(pool, job, "test-request-id", sqslistener.response_queue, request_message)

        response_yaml = yaml.safe_load(completed_message_body)
        assert response_yaml['result'] == 'success'

        boto_sqs_patcher.stop()