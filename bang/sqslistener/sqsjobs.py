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
import os
from request_message import RequestMessage
import logging


logger = logging.getLogger("SQSListener")

class SQSJobs():
    """SQS Jobs"""
    def __init__(self):
        pass

    def load_jobs_from_yaml_object(self, yaml_object):
        self.jobs_yaml = yaml_object

    def load_jobs_from_file(self, jobs_definition_path):
        if os.path.exists(jobs_definition_path):
            with open(jobs_definition_path, 'rt') as f:
                self.jobs_yaml = yaml.load(f.read())
        else:
            raise Exception("No job definition found at: " + jobs_definition_path)

    def generate_job(self, job_name, job_id, parameters=()):
        try:
            bang_stacks = self.jobs_yaml[job_name]["bang-stacks"]
            return SQSJob(job_name, bang_stacks, parameters)

        except KeyError, e:
            logger.error("YAML missing key in jobs config: %s" % str(e))

        return None

class SQSJob():
    """A single job"""
    def __init__(self, name, bang_stacks, parameters=None):
        self.name = name
        self.bang_stacks = bang_stacks  # Paths to yaml files to be merged for job.
        self.parameters = parameters



