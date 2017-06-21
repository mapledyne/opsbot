"""Commands available by the slackbot and some related helper functions."""
import json
import random
from six import iteritems
import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from datetime import datetime, timedelta
import fnmatch

import config
from people import People
from people import Level
from strings import Strings
import sql

user_list = People()
maybe = []

# Build our word list:
with open(config.WORDPATH) as w:
    wordlist = w.readlines()
for word in wordlist:
    maybe.append(word.strip())


def pass_good_until(hours_good=config.HOURS_TO_GRANT_ACCESS):
    """Find time that a password is good until."""
    return datetime.now() + timedelta(hours=hours_good)


def friendly_time(time=None):
    """Rerurn the time in a print-friendly format."""
    if time is None:
        time = pass_good_until()
    return time.strftime(config.TIME_PRINT_FORMAT)


def generate_password(pass_fmt=config.PASSWORD_FORMAT):
    """Return a new password, using pass_fmt as a template.

    This is a simple replacement:
        # ==> a number from 0-99
        * ==> a word from the wordlist
        ! ==> a symbol
    """
    random.shuffle(maybe)

    new_pass = pass_fmt
    loc = 0
    while '*' in new_pass:
        new_pass = new_pass.replace("*", maybe[loc], 1)
        loc = loc + 1
        if loc == len(maybe):
            random.shuffle(maybe)
            loc = 0
    while '#' in new_pass:
        new_pass = new_pass.replace("#", str(random.randint(0, 99)), 1)
    while '!' in new_pass:
        new_pass = new_pass.replace(
            "!", random.choice(config.PASSWORD_SYMBOLS))
    return new_pass


def load_users(everyone):
    """Load slack user data into the People object."""
    if user_list.loaded:
        return
    for user in iteritems(everyone):
        user_list.load(user[1])


def list_to_names(names):
    """Return just the names from user objects from the names object.

    Given a list of Person objects (typically a subset of the People object)
    reduce the list from Person objects just to a simple array of their
    names.
    """
    names_list = []
    for n in names:
        names_list.append(names[n].details['name'])
    return names_list


def pretty_json(data, with_ticks=False):
    """Return the JSON data in a prettier format.

    If with_ticks is True, include ticks (```) around it to have it in
    monospace format for better display in slack.
    """
    pretty = json.dumps(data, sort_keys=True, indent=4)
    if with_ticks:
        pretty = '```' + pretty + '```'
    return pretty


def find_channel(channels, user):
    """Return the direct message channel of a user, if it exists."""
    for x in channels:
        if 'is_member' in channels[x]:
            continue
        if channels[x]["user"] == user:
            return channels[x]["id"]
    return ""


def have_channel_open(channels, user):
    """Return True if the user as a DM channel open with the bot."""
    for x in channels:
        chan = channels[x]
        if 'is_member' in chan:
            continue
        if chan['user'] == user:
                return True
    return False


@respond_to('channels')
def channels(message):
    """Display summary of channels in Slack."""
    load_users(message._client.users)
    for x in message._client.channels:
        chan = message._client.channels[x]
        if 'is_member' in chan:
            if chan['is_member']:
                message.reply("{} ({})".format(chan['name'], chan['id']))
#                message.reply(pretty_json(chan, True))
        elif 'is_im' in chan:
            print(chan)
            friendlyname = chan['user']
            try:
                friendlyname = chan['user'].name
            except KeyError:
                pass
            message.reply("User channel: {} ({})".format(friendlyname,
                                                         chan['id']))
#            message.reply(pretty_json(chan, True))


@respond_to('password$')
@respond_to('password (\d*)')
def pass_multi_request(message, num_words=1):
    """Display a generated password for the user."""
    try:
        tries = int(num_words)
    except ValueError:
        message.reply(Strings['NONSENSE'])
        return
    if (tries > 10):
        message.reply(Strings['TOO_MANY_PASSWORDS'])
        return
    if (tries < 1):
        message.reply(Strings['NONSENSE'])
        return
    for x in range(tries):
        message.reply("```" + generate_password() + "```")


@respond_to('help', re.IGNORECASE)
@listen_to('help', re.IGNORECASE)
def channel_help(message):
    """Reply with the link to the help doc url."""
    message.reply(Strings['HELP'].format(config.HELP_URL))


@respond_to('^approve me$', re.IGNORECASE)
def approve_me(message):
    """Send request to be approved to the approvers/admins."""
    load_users(message._client.users)
    sender_id = message._get_user_id()
    target = user_list[sender_id].details['name']
    if (user_list[sender_id].is_unknown):
        message.reply(Strings['APPROVER_REQUEST'])
        names = list_to_names(user_list.admin_list())
        approval_message = Strings[
            'APPROVER_REQUEST_DETAIL'].format(">, <@".join(names), target)
        message._client.send_message(Config.AUTH_CHANNEL, approval_message)
    else:
        message.reply(
            "Your status is already: " + user_list[sender_id].level.name)


@listen_to('^approve me$', re.IGNORECASE)
def approve_me_group(message):
    """Reply to 'approve me' in the group channel (redirect to a DM)."""
    load_users(message._client.users)
    sender_id = message._get_user_id()

    if (user_list[sender_id].is_unknown):
        message.reply(Strings['APPROVE_ME_REQUEST'])
    else:
        self_name = user_list[sender_id].level.name
        message.reply("Your status is already: {}".format(self_name))


@listen_to('^approve (\S*)$')
def approve_person(message, target):
    """Approve a user, if the author of the msg is an admin."""
    load_users(message._client.users)
    if target == 'me':
        return
    user = user_list.find_user(target)

    approver = message._get_user_id()
    if user_list[approver].is_admin:
        if user is not None:
            target_name = user.details['name']
            if user.is_unknown:
                message.reply("Approving user: '{}'".format(target_name))
                user_list[user.details['id']].level = Level.Approved
                user_list.save()
            elif user.is_denied:
                message.reply(Strings['MARKED_DENIED'])
            else:
                message.reply("{} is already: {}.".format(target_name,
                                                          user.level.name))
        else:
            message.reply(Strings['USER_NOT_FOUND'].format(target))
    else:
        message.reply(Strings['CANT_APPROVE'])


@respond_to('^admins$')
def admin_list(message):
    """Display a list of all admins."""
    load_users(message._client.users)
    names = list_to_names(user_list.admin_list())
    message.reply('My admins are: {}'.format(", ".join(names)))


@respond_to('^approved$')
def approved_list(message):
    """Display a list of all approved users."""
    load_users(message._client.users)
    names = list_to_names(user_list.approved_list())
    message.reply('Approved users are: {}'.format(", ".join(names)))


@respond_to('^denied$')
def denied_list(message):
    """Display a list of denied users."""
    load_users(message._client.users)
    names = list_to_names(user_list.denied_list())
    message.reply('Denied user are: {}'.format(", ".join(names)))


@respond_to('^unknown$')
def unknown_list(message):
    """Display a list of users without a known status."""
    load_users(message._client.users)
    names = list_to_names(user_list.unknown_list())
    if (len(names) > 100):
        message.reply(Strings['TOO_MANY_USERS'].format(len(names)))
        return
    message.reply('Unknown users are: {}'.format(", ".join(names)))


@respond_to('^me$')
def status(message):
    """Display the JSON data of the messaging user."""
    message.reply('User_id: ' +
                  str(message._client.users[message._get_user_id()]))


@respond_to('^body$')
def body(message):
    """Display the JSON data of this message.

    Mainly (only?) useful for understanding the JSON options available
    a message.
    """
    message.reply(str(message._body))


@respond_to('^users$')
def users(message):
    """Display number of total Slack users."""
    user_list = []
    for userid, user in iteritems(message._client.users):
        user_list.append(user["name"])
    message.reply(Strings['USERS_FOUND'].format(len(user_list)))


@respond_to('^search (.*)')
def search_user(message, search):
    """Return users found from a search."""
    found = []
    search = search.lower()
    for userid, user in iteritems(message._client.users):
        if search in user['name'].lower():
            found.append('{} ({})'.format(user['name'], userid))
    if len(found) == 0:
        message.reply('No user found by that key: {}.'.format(search))
        return
    message.reply('Users found: {}'.format(', '.join(found)))


@respond_to('^details (.*)')
def find_user_by_name(message, username):
    """Reurn the JSON of a given user."""
    for userid, user in iteritems(message._client.users):
        if user['name'] == username:
            message.reply(pretty_json(user, True))
            if (have_channel_open(message._client.channels, userid)):
                message.reply('User has a channel open.')
            else:
                message.reply("User doesn't have a channel open.")
            return
    message.reply('No user found by that name: {}.'.format(username))


@respond_to('^server (\S*)$')
@listen_to('^server (\S*)$')
def find_server(message, db):
    """Display the server a given database is on."""
    db_list = sql.database_list()
    if db in db_list:
        server = db_list[db]
        message.reply(Strings['DATABASE_SERVER'].format(db, server))
    else:
        message.reply(Strings['DATABASE_UNKNOWN'].format(db))


@listen_to('^grant (\S*)$')
def no_reason(message, db):
    """Display error when no reason given trying to 'grant' access."""
    message.reply(Strings['GRANT_EXAMPLE'].format(db))


def grant_sql_access(message, db, reason, readonly):
    """Grant access for the user to a the specified database."""
    db_list = sql.database_list()
    requested_dbs = fnmatch.filter(db_list, db)
    load_users(message._client.users)
    requester = message._get_user_id()
    if user_list[requester].is_approved:
        if (len(requested_dbs)) == 0:
            message.reply(Strings['DATABASE_UNKNOWN'].format(db))
            return

        password = generate_password()
        chan = find_channel(message._client.channels, message._get_user_id())
        offset = int(user_list[requester].details['tz_offset'])
        expiration = pass_good_until() + timedelta(seconds=offset)
        created_flag = False
        for db in requested_dbs:
            created = sql.create_sql_login(user_list[requester].name,
                                           password,
                                           db,
                                           expiration,
                                           readonly,
                                           reason)
            # We want to remember if the password was ever created so we
            # can have a message about it.
            if created:
                created_flag = True
        friendly_exp = friendly_time(expiration)
        message.reply(Strings['GRANTED_ACCESS'].format(db, friendly_exp))
        if (len(requested_dbs) > 1):
            message.reply('{} databases affected.'.format(len(requested_dbs)))
        if created_flag:
            pass_created = Strings['PASSWORD_CREATED'].format(db, password)
            message._client.send_message(chan, pass_created)
        else:
            pass_reused = Strings['PASSWORD_REUSED'].format(db)
            message._client.send_message(chan, pass_reused)
        slack_id_msg = Strings['SLACK_ID'].format(user_list[requester].name)
        message._client.send_message(chan, slack_id_msg)
        return
    if user_list[requester].is_denied:
        message.reply('Request denied')
        return
    message.reply(Strings['NOT_APPROVED_YET'])


@listen_to('^grant (\S*) (.*)')
def grant_access(message, db, reason):
    """Request read only access to a database."""
    grant_sql_access(message, db, reason, True)


@listen_to('^grantrw (\S*) (.*)')
def grant_access(message, db, reason):
    """Request read/write access to a database."""
    grant_sql_access(message, db, reason, False)
