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
from sqslistener_callbacks import SQSListenerPlaybookCallbacks, SQSListenerPlaybookRunnerCallbacks
import ansible
from ansible.callbacks import verbose

import logging
logger = logging.getLogger("SQSListener")

### Monkey patch to grab logged output from paramiko for sqslister logs instead. ###
def monkey_patched_verbose(msg, host=None, caplevel=2):
    """ Overrides output given by paramiko.
        Rationale: This seemed a lot better than copying and pasting the whole library and fixing the output
                   wherever I found it.
    """
    logger.info("%s - %s" % (host, msg))

ansible.callbacks.verbose = monkey_patched_verbose
logger.debug("Note that ansible.callbacks.verbose has been monkey patched!")
### End monkey patch ###


def start_job_process(pool, job, request_id):
    if job is not None:
        result = pool.apply_async(perform_job, [job, request_id])
        return result.get()
    else:
        logger.error("Job with request_id %s, does not exist." % str(request_id))


def perform_job(job, request_id):
    try:
        config = Config.from_config_specs(job.bang_stacks)
        stack = Stack(config)
        stack.deploy()

        ansible_callbacks = stack.configure(playbook_callbacks_class=SQSListenerPlaybookCallbacks,
                                            playbook_runner_callbacks_class=SQSListenerPlaybookRunnerCallbacks)
        ansible_callbacks.log_summary()

    except Exception as e:
        logger.exception(e)
        yaml_response = ResponseMessage(job.name, request_id, "failure",
                                        "%s. See sqslistener logs for a complete stack trace." % str(e))
        return yaml_response.dump_yaml()

    yaml_response = ResponseMessage(job.name, request_id, "success")
    return yaml_response.dump_yaml()
