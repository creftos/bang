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
from boto.sqs.message import Message

logger = logging.getLogger("SQSListener")

class RequestMessageException(Exception):
    pass

class MissingDataRequestMessageException(RequestMessageException):
    pass

class NoneMessageRequestMessageException(MissingDataRequestMessageException):
    pass

class InvalidMessageException(RequestMessageException):
    pass

class MissingRequestIdRequestMessageException(MissingDataRequestMessageException):
    pass

class EmptyBodyRequestMessageException(MissingDataRequestMessageException):
    pass

class MissingRequestIdRequestMessageException(MissingDataRequestMessageException):
    pass

class MissingJobNameRequestMessageException(MissingDataRequestMessageException):
    pass


class RequestMessage:
    def __init__(self, message=None):
        if message is None:
            raise NoneMessageRequestMessageException("Message was not instantiated.")
        if type(message) is Message:
            yaml_message_body = message.get_body()
            self.parse_yaml(yaml_message_body)
        else:
            raise InvalidMessageException("Incoming Message was invalid. Was not converted to boto Message type:\n%s" % str(message))

    def parse_yaml(self, message_body):
        if message_body is None:
            raise EmptyBodyRequestMessageException("Message body cannot be None.")

        yaml_message_body = yaml.safe_load(message_body)
        if yaml_message_body is None:
            raise EmptyBodyRequestMessageException("Can't have an empty message body.")

        try:
            self.job_name = yaml_message_body.keys()[0]
        except AttributeError, e:
            raise MissingJobNameRequestMessageException("Unable to get job name yaml key from message: %s" % str(e))

        if yaml_message_body[self.job_name] is None:
            raise MissingJobNameRequestMessageException("Request messages must contain a body.")

        if "request_id" not in yaml_message_body[self.job_name]:
            raise MissingRequestIdRequestMessageException("Request messages must contain a request id.")

        self.request_id = yaml_message_body[self.job_name]['request_id']
        if yaml_message_body[self.job_name].has_key("parameters"):
            self.job_parameters = yaml_message_body[self.job_name]["parameters"]
        else:
            self.job_parameters = None

