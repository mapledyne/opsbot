import json
import random
from six import iteritems
import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from datetime import datetime, timedelta

from people import People

wordpath = 'opsbot/wordlist.txt'

user_list = People()

maybe = []

with open(wordpath) as w:
    wordlist = w.readlines()

for word in wordlist:
    maybe.append(word.strip())


def pass_good_until():
    return datetime.now() + timedelta(hours=4)


def friendly_time(time=None):
    if time is None:
        time = pass_good_until()
    return time.strftime('%b-%d %I:%M%p')


def generate_password():
    random.shuffle(maybe)
    newpass = (maybe[0] +
               str(random.randint(0, 99)) +
               maybe[1] +
               str(random.randint(0, 99)) +
               maybe[2])
    return newpass


def load_users(everyone):
    if user_list.loaded:
        return
    for user in iteritems(everyone):
        user_list.load(user[1])


def list_to_names(names):
    names_list = []
    for n in names:
        names_list.append(names[n].details['name'])
    return names_list

def pretty_json(data, with_ticks=False):
    pretty = json.dumps(data, sort_keys=True, indent=4)
    if with_ticks:
        pretty = '```' + pretty + '```'
    return pretty


@respond_to('channels')
def channels(message):
    for x in message._client.channels:
        chan = message._client.channels[x]
        if 'is_member' in chan:
            if chan['is_member']:
                message.reply(pretty_json(chan, True))
        elif 'is_im' in chan:
            message.reply(pretty_json(chan, True))

@respond_to('password$')
@respond_to('password (\d*)')
def pass_multi_request(message, num_words=1):
    tries = int(num_words)
    if (tries > 10):
        message.reply("I can't generate that many passwords at one time.")
        return
    if (tries < 1):
        message.reply("That doesn't make any sense.")
        return
    for x in range(tries):
        message.reply("```" + generate_password() + "```")

@respond_to('help', re.IGNORECASE)
#@listen_to('help', re.IGNORECASE)
def channel_help(message):
    url = ('https://mcgops.atlassian.net'
           '/wiki/display/HO/McgAuthBot+commands+and+help')
    message.reply('Help document for me lives at: {}'.format(url))

@respond_to('approve', re.IGNORECASE)
def approve_me(message):
    sender_id = message._get_user_id()
    level = user_list[sender_id].level
    if (level == UNKNOWN):
        message.reply("Sending request to the approvers to have you be approved.")
    else:
        message.reply("Your status is alredy: " + user_list[sender_id].level.name)


@respond_to('admins')
def admin_list(message):
    load_users(message._client.users)
    names = list_to_names(user_list.admin_list())
    message.reply('My admins are: {}'.format(", ".join(names)))


@respond_to('approved')
def approved_list(message):
    load_users(message._client.users)
    names = list_to_names(user_list.approved_list())
    message.reply('Approved users are: {}'.format(", ".join(names)))


@respond_to('denied')
def denied_list(message):
    load_users(message._client.users)
    names = list_to_names(user_list.denied_list())
    message.reply('Denied user are: {}'.format(", ".join(names)))


@respond_to('unknown')
def unknown_list(message):
    load_users(message._client.users)
    names = list_to_names(user_list.unknown_list())
    if (len(names) > 100):
        message.reply("I have too many unknown users ({}) and can't list them all.".format(len(names)))
        return
    message.reply('Unknown users are: {}'.format(", ".join(names)))

@respond_to('me')
def status(message):
    message.reply('User_id: ' +
                  str(message._client.users[message._get_user_id()]))


@respond_to('body')
def body(message):
    message.reply(str(message._body))


@respond_to('users')
def users(message):
    user_list = []
    for userid, user in iteritems(message._client.users):
        user_list.append(user["name"])
    message.reply("{} users found. Try 'search <name>' to find someone.".format(len(user_list)))


@respond_to('search (.*)')
def search_user(message, search):
    found = []
    search = search.lower()
    for userid, user in iteritems(message._client.users):
        if search in user['name'].lower():
            found.append('{} ({})'.format(user['name'], userid))
    if len(found) == 0:
        message.reply('No user found by that key: {}.'.format(search))
        return
    message.reply('Users found: {}'.format(', '.join(found)))


@respond_to('details (.*)')
def find_user_by_name(message, username):
    for userid, user in iteritems(message._client.users):
        if user['name'] == username:
            message.reply(pretty_json(user, True))
            return
    message.reply('No user found by that name: {}.'.format(username))

@listen_to('grant (\S*) (.*)')
def grant_access(message, db, reason):
    load_users(message._client.users)
    requester = message._get_user_id()
    if user_list[requester].is_approved:
        expiration = pass_good_until() + timedelta(seconds=int(user_list[requester].details['tz_offset']))
        message.reply('Granting access to: {}'.format(db))
        message.reply('Reason: {}'.format(reason))
        message.reply('Password: {}'.format(generate_password()))
        message.reply('Good until: {}'.format(friendly_time(expiration)))
        return
    if user_list[requester].is_denied:
        message.reply('Request denied')
        return
    message.reply("Unfortunately, you're not approved yet. Requesting approval.")
