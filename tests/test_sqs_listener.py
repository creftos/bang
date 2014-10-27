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
import boto.Message
from bang.sqslistener.sqslistener import SQSListener
import logging

class TestJobs(unittest.TestCase):
    def test_import_jobs(self):
        listener = SQSListener()

        test_job_name = listener.jobs.get("name")

        self.assertEqual("example job", test_job_name)
        pass # TODO Placeholder

    def test_parse_job(self):
        job = ( "---"
                "name: test_job_1"
                "path: sqs-listener-examples/example-job-1.yml"
                "parameters:"
                "- param1"
                "- param2"
                "- param3" )

        listener = SQSListener()
        pass # TODO Placeholder