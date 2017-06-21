"""Background tasks needed to support the slack bot."""
import json
import logging
import threading
import time

import config
from people import People
from people import Level
from strings import Strings
import sql


class TaskThread(threading.Thread):
    """Base for all task threads.

    This essentially is just a regular thread that manages itself
    and has the ability be asked to stop.

    Template for making a new thread with this class:

    class NewThread(TaskThread):
        def thread_worker(self):
            # Do work here.

    By default the thread will do that work evert THREAD_WORK_TIMER interval
    (set in config.py). Change self.thread_work_timer if it should be
    different for this thread.
    """

    def __init__(self):
        """Create a TaskThread."""
        super(TaskThread, self).__init__()
        self._stop_event = threading.Event()
        self.thread_sleep = config.THREAD_SLEEP
        self.thread_work_timer = config.THREAD_WORK_TIMER
        self._time = 0
        logging.debug('Creating {} thread.'.format(self.name))

    @property
    def name(self):
        """Return the name of our class."""
        return self.__class__.__name__

    @property
    def ready_to_work(self):
        """Return True if our wait time has expired (thread_work_timer)."""
        return self._time + self.thread_work_timer < time.time()

    @property
    def stopped(self):
        """Return True if the stop event flag is set."""
        return self._stop_event.is_set()

    def stop(self):
        """Stop the thread - set the stop event flag.

        This will cause the thread to stop, but it'd be polite to
        run join() after running stop() in order to have the parent thread
        wait for everything to complete.
        """
        logging.debug('Reqesting thread {} to stop.'.format(self.name))
        self._stop_event.set()

    def run(self):
        """Check to see if we should do work and/or exit."""
        while not self.stopped:
            time.sleep(self.thread_sleep)
            if self.ready_to_work:
                logging.debug('Running work for {} thread.'.format(self.name))
                self._time = time.time()
                self.thread_worker()

    def thread_worker(self):
        """The actual work of one of these threads.

        Override this to do any work in these threads.
        """
        pass


class DeleteUser(TaskThread):
    """Check user list and delete any users that are past their exp date."""

    def thread_worker(self):
        """Check users and delete when appropriate."""
        logging.debug('Checking users to delete.')
        sql.delete_expired_users()


class DBList(TaskThread):
    """Maintain the list of databases."""

    def thread_worker(self):
        """Get a list of sql databases."""
        logging.debug('Updating database list.')
        sql.build_database_list()
