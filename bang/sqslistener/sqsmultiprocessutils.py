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

from bang.config import Config
from bang.stack import Stack
from response_message import ResponseMessage
import logging

logger = logging.getLogger("SQSListener")


def start_job_process(pool, job, request_id):
    result = pool.apply_async(perform_job, [job, request_id])
    return result.get()


def perform_job(job, request_id):
    try:
        config = Config.from_config_specs(job.bang_stacks)
        stack = Stack(config)
        stack.deploy()
        ansible_callbacks = stack.configure()
        ansible_callbacks.log_summary()

    except Exception as e:
        logger.exception(e)
        yaml_response = ResponseMessage(job.name, request_id, False,
                                        "%s. See sqslistener logs for a complete stack trace." % str(e))
        return yaml_response.dump_yaml()

    yaml_response = ResponseMessage(job.name, request_id, True)
    return yaml_response.dump_yaml()
