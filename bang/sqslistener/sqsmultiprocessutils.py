from multiprocessing import Pool
from boto.sqs.message import Message

def start_job_process(pool, job):
    result = pool.apply_async(perform_job, [job,]) # TODO: Add callback to send a response when completed.
    return result.get()

def perform_job(job):
    job.perform()

