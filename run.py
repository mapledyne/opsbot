"""Slackbot main run.py file.

Set up the slack bot and any surrounding work needed to create SQL
access for users.
"""

import logging
import threading
import time

from slackbot.bot import Bot

import opsbot.config as config
import opsbot.tasks

logging.basicConfig(level=config.LOGGING_LEVEL)

task_threads = []


def bot_worker():
    """Put the bot in its own thread."""
    bot = Bot()
    bot.run()


def main():
    """Kick off the bot and such.

    This is what is run when the script is run via command line.
    """
    db_list_task = opsbot.tasks.DBList()
    db_list_task.thread_work_timer = config.CHECK_DATABASE_INTERVAL
    task_threads.append(db_list_task)

    delete_user_task = opsbot.tasks.DeleteUser()
    task_threads.append(delete_user_task)

    for task in task_threads:
        task.start()

    bot_thread = threading.Thread(target=bot_worker)
    bot_thread.daemon = True
    bot_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info('Keyboard Interrupt detected. Exiting.')
        for task in task_threads:
            task.stop()
            task.join()


if __name__ == "__main__":
    main()
