import json
import random
from slackbot.bot import respond_to

wordpath = '/opt/words/wordlist.txt'
people_path = '/opt/opsbot/people.json'

people = {}
maybe = []

with open(wordpath) as w:
    wordlist = w.readlines()

for word in wordlist:
    maybe.append(word.strip())


def load_people():
    with open(people_path) as data_file:
        people = json.load(data_file)
    return people

people = load_people()

def generate_password():
    random.shuffle(maybe)
    newpass = maybe[0] + str(random.randint(0, 99)) + maybe[1] + str(random.randint(0, 99)) + maybe[2]
    return newpass


@respond_to('password')
def pass_request(message):
    message.reply(generate_password())


@respond_to('admins')
def pass_request(message):
    message.reply('My admins are: {}'.format(", ".join(people['admins'])))


@respond_to('status')
def status(message):
    message.reply('User_id: ' + str(message._client.users[message._get_user_id()]))
    print(message._body)

@respond_to('users')
def users(message):
    message.reply('Users: {}'.format(", ".join(message._client.users)))

