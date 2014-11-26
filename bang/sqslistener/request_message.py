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

import yaml
import logging

logger = logging.getLogger("SQSListener")

class RequestMessage:
    def __init__(self, message=None):
        if message is not None:
            try:
                yaml_message_body = message.get_body()
                self.parse_yaml(yaml_message_body)

            except Exception as e:
                logger.error("Request Message failure, see exception:")
                logger.error(e)
        else:
            raise Exception("Message Body required.")

    def parse_yaml(self, yaml_message_body):
        yaml_message_body = yaml.load(yaml_message_body)
        self.job_name = yaml_message_body.keys()[0]
        # if "request_id" not in yaml_message_body[self.job_name]:
        #     print "not there"
        #     raise yaml.YAMLError("Request messages must contain a request id.")

        self.request_id = yaml_message_body[self.job_name]['request_id']

        print "ajsdlkfjlkasdjlkf : %s" % self.request_id

        if yaml_message_body[self.job_name].has_key("parameters"):
            self.job_parameters = yaml_message_body[self.job_name]["parameters"]
        else:
            self.job_parameters = None

