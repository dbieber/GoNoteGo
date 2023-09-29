from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore  # noqa: F401
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

import parsedatetime


# Global executor to be set by runner.
executor_singleton = None


def execute_command(cmd):
  executor_singleton.execute(cmd)


class Scheduler:

  def __init__(self, start=True):
    self.scheduler = BackgroundScheduler(executors={
        'default': ThreadPoolExecutor(20),
        'processpool': ProcessPoolExecutor(5)
    })
    self.scheduler.add_jobstore(
        'redis',
        jobs_key='GoNoteGo:jobs',
        run_times_key='GoNoteGo:run_times'
    )

    if start:
      print('Starting')
      self.scheduler.start()
      print('Continuing')
    self.datetime_parser = parsedatetime.Calendar()

  def parse(self, at):
    return self.datetime_parser.parseDT(at)[0]

  def already_scheduled(self, what):
    # TODO(Bieber): Improve efficiency with a dict
    for scheduled_at, scheduled_what in self.get_jobs():
      if what == scheduled_what:
          return True
    return False

  def schedule(self, at, what):
    dt = self.parse(at)
    trigger = DateTrigger(dt)
    self.scheduler.add_job(
        execute_command,
        trigger=trigger,
        args=[what.strip()],
    )

  def get_jobs(self):
    jobs = self.scheduler.get_jobs()
    return [(job.next_run_time, job.args[0]) for job in jobs]
