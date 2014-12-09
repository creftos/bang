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

class RequestMessageException(Exception):
    pass

class RequestMessage:
    def __init__(self, message=None):
        if message is not None:
            yaml_message_body = message.get_body()
            self.parse_yaml(yaml_message_body)
        else:
            raise RequestMessageException("Message Body required.")

    def parse_yaml(self, message_body):
        yaml_message_body = yaml.safe_load(message_body)
        if yaml_message_body is None:
            raise RequestMessageException("Can't have an empty message body.")

        try:
            self.job_name = yaml_message_body.keys()[0]
        except AttributeError:
            raise RequestMessageException("Unable to get job name yaml key from message.")

        if yaml_message_body[self.job_name] is None or "request_id" not in yaml_message_body[self.job_name]:
            raise RequestMessageException("Request messages must contain a request id.")

        self.request_id = yaml_message_body[self.job_name]['request_id']
        if yaml_message_body[self.job_name].has_key("parameters"):
            self.job_parameters = yaml_message_body[self.job_name]["parameters"]
        else:
            self.job_parameters = None

