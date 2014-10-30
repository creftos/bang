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

import os
import yaml
import logging, logging.config
import time
import boto.sqs
from sqsjobs import SQSJobs
from boto.sqs.message import Message
from boto.exception import SQSError
from multiprocessing import Pool
from sqsmultiprocessutils import start_job_process

LOGGING_CONFIG_PATH = "logging-conf.yml"
SQS_LISTENER_CONFIG_PATH = "sqs-listener-conf.yml"
JOBS_CONFIG_PATH = "jobs.yml"
DEFAULT_POOL_PROCESSES = 5

DEFAULT_CONFIG_LEVEL = logging.DEBUG

class SQSListener:
    def __init__(self,
                 aws_region="us-east-1",
                 queue_name="bang-queue",
                 response_queue_name="bang-response",
                 polling_interval=2):

        ### Set up logging ###
        if os.path.exists(LOGGING_CONFIG_PATH):
            with open(LOGGING_CONFIG_PATH, 'rt') as f:
                config = yaml.load(f.read())

            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level = DEFAULT_CONFIG_LEVEL)

        self.logger = logging.getLogger("SQSListener")

        self.logger.debug("Starting up SQS Listener...")

        try:
            self.logger.debug("Connecting to SQS...")
            self.conn = boto.sqs.connect_to_region(aws_region)
            self.queue = self.conn.get_queue(queue_name)
            self.response_queue = self.conn.get_queue(response_queue_name);

            if self.queue is None:
                self.logger.CRITICAL("Queue " + queue_name + " does not exist.")
                raise Exception("Queue " + queue_name + " does not exist.")
            if self.response_queue is None:
                self.logger.CRITICAL("Queue " + response_queue_name + " does not exist.")
                raise Exception("Queue " + response_queue_name + " does not exist.")

        except SQSError:
            print "An error occurred setting up an SQS Connection."

        self.job_set = SQSJobs()
        self.job_set.load_jobs_from_file(JOBS_CONFIG_PATH)

        self.polling_interval = polling_interval
        self.pool = Pool(processes=DEFAULT_POOL_PROCESSES)

        self.logger.debug("Set up complete.")


    def post_response(self, response):
        """Post a response to the response queue."""
        message = Message()
        message.set_body(response)
        self.response_queue.write(message)

    def poll_queue(self):
        try:
            polling_response = self.queue.get_messages()

            for message in polling_response:
                self.process_message(message)

        except SQSError:
            print "An error occurred polling a queue."

    def process_message(self, message):
        try:
            # log message here.
            yaml_message_body = yaml.load(message.get_body())
            job_name = yaml_message_body.keys()[0]
            self.logger.info("Processing message " + job_name)

            if yaml_message_body[job_name].has_key("parameters"):
                job_parameters = yaml_message_body[job_name]["parameters"]
            else:
                job_parameters = ()

            job = self.job_set.generate_job(job_name, job_parameters)

            start_job_process(self.pool, job)

            self.queue.delete_message(message)
            self.post_response("Received Job: " + job_name)

        except SQSError:
            self.logger.ERROR("An error occurred processing a message")
            print "An error occurred processing a message."


    def load_sqs_listener_config(self, filename):
        self.logger.info("Loading general sqs listener config from file: " + filename)

    def start_polling(self):
        self.logger.info("Starting polling")
        self.polling = True

        while self.polling:
            self.poll_queue()
            time.sleep(self.polling_interval)

    def stop_polling(self):
        self.logger.info("Stopping polling")
        self.polling = False