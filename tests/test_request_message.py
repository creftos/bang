#!/usr/bin/python
# Copyright 2014 - Brian J. Donohoe
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
from boto.sqs.message import Message

from bang.sqslistener.request_message import RequestMessage


class TestRequestMessage(unittest.TestCase):

    def test_parse_yaml(self):

        message_body=("---\n"
                      "test_job_1:\n"
                      "  request_id: 12\n")

        message = Message(body=message_body)

        request_message = RequestMessage(message)

        assert request_message.job_name == 'test_job_1'
        assert request_message.request_id == 12








