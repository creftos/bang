import yaml

# Not sure I like this idea, since we would have to reparse and reload this stuff every time there's a change instead
#   just reloading the yaml file and parsing on the fly.

class SQSJobs():
    """"SQS Jobs"""
    def __init__(self):
        self.job_list = []

    def add_job(self, job):
        self.job_list.append(job)

    def read_jobs_config(self, yaml_filename):
        pass

class SQSJob():
    """A single job"""
    def __init__(self, name="", yaml_paths=("",)):
        self.name = name
        self.yaml_paths = yaml_paths # Paths to yaml files to be merged for job.

    def parseYamlJob(self, yaml_string):
        self.name = yaml_string("name")
        self.yaml_paths = yaml_string("paths")

