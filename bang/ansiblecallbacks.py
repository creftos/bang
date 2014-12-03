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

import logging

logger = logging.getLogger("SQSListener")

class AnsibleCallbacks(object):

    def __init__(self, stats, playbook_cb, runner_cb):
        self.stats = stats
        self.playbook_cb = playbook_cb
        self.runner_cb = runner_cb

    def log_summary(self):
        hosts = sorted(self.stats.processed.keys())
        failed = False
        for h in hosts:
            hsum = self.stats.summarize(h)
            if hsum['failures'] or hsum['unreachable']:
                failed = True
            logger.info("%-30s : %s" % (h, hsum))