import yaml
import os

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

    def generate_job(self, job_name, parameters=()):
        try:
            bang_stacks = self.jobs_yaml[job_name]["bang-stacks"]
            return SQSJob(job_name, bang_stacks, parameters)

        except KeyError, e:
            logging.error("YAML missing key in jobs config: %s" % str(e))

        return None

class SQSJob():
    """A single job"""
    def __init__(self, name, bang_stacks, parameters=None):
        self.name = name
        self.bang_stacks = bang_stacks  # Paths to yaml files to be merged for job.
        self.parameters = parameters

    def perform(self):
        # TODO: Invoke bang here
        pass



