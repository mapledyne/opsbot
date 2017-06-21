"""Settings specific to the slackbot."""

import opsbot.config as config

DEFAULT_REPLY = "Sorry but I didn't understand you"
ERRORS_TO = config.SLACK_ERROR_TARGET

PLUGINS = ['opsbot.commands']
