# Copyright 2014 - Brian J Donohoe
#
# This file is part of bang.
#
# bang is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# bang is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with bang.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import mock
from boto.sqs.queue import Queue
from bang.sqslistener.sqslistener import SQSListener
import boto
import boto.sqs.connection
from boto.sqs.connection import SQSConnection


class TestSQSListener(unittest.TestCase):

    mockedConnection = mock.Mock()
    mockedConnection.return_value = SQSConnection()
    def setUp(self):
        self.sqsListener = SQSListener(jobs_config_path='resources/sqslistener/jobs.yml')

    @mock.patch.object(Queue, 'write')
    def test_post_response(self, mock_write_method):
        self.sqsListener.post_response("Message Body Test")
        assert mock_write_method.called

    @mock.patch.object(Queue, 'write')
    def post_response_test(self, mock_write_method):
        self.sqsListener.post_response("Message Body Test")
        assert mock_write_method.called

    @mock.patch.object(Queue, 'get_messages')
    def poll_queue_test(self, mock_get_messages_method):
        self.sqsListener.poll_queue()
        assert mock_get_messages_method.called

    @mock.patch('bang.sqslistener.sqslistener.SQSListener.post_response')
    def process_message_test(self, mock_post_response):
        # TODO: Process message does several other things that need to be tested.
        # TODO: I need to look into mocking actual return values of things as well.
        message = boto.sqs.message.Message()
        self.sqsListener.process_message(message)
        assert mock_post_response.called

    def load_sqs_listener_config_test(self):
        pass

    def start_polling_test(self):
        pass

    def stop_polling_test(self):
        pass


class TestSQSListenerNoSetup(unittest.TestCase):
    @mock.patch('boto.sqs.connect_to_region')
    def setup_conn_test(self,
                   mock_connect_to_region):

        self.sqsListener = SQSListener(
            aws_region="test-region",
            queue_name="test-queue",
            response_queue_name="test-response-queue",
            polling_interval=99,
            jobs_config_path='resources/sqslistener/jobs.yml'
            logging_config_path='resources/sqslistener/logging-conf.yml',)

        assert mock_connect_to_region.called


