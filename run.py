import json
import random
from slackbot.bot import Bot
from slackbot.bot import respond_to

wordpath = '/opt/words/wordlist.txt'
people_path = '/opt/opsbot/people.json'
people = {}
maybe = []


def load_people():
    with open(people_path) as data_file:
        people = json.load(data_file)


def generate_password():
    random.shuffle(maybe)
    newpass = maybe[0] + str(random.randint(0, 99)) + maybe[1] + str(random.randint(0, 99)) + maybe[2]
    return newpass


@respond_to('password')
def pass_request(message):
    message.reply(generate_password())

@respond_to('admins')
def pass_request(message):
    message.reply('My admins are: {}'.format(", ".join(people[admins])))


def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    with open(wordpath) as w:
        wordlist = w.readlines()

    for word in wordlist:
        maybe.append(word.strip())

    load_people()
    main()
