from enum import IntEnum
import json

people_path = '/opt/opsbot/people.json'


class Level(IntEnum):
    Admin = 50
    Unknown = 0
    Denied = -10
    Approved = 10


class Person:
    def __init__(self, level):
        self.level = Level(level)
        self.details = {}

    @property
    def loaded(self):
        return len(self.details) > 0

    @property
    def is_admin(self):
        return self.level == Level.Admin

    @property
    def is_approved(self):
        return self.level >= Level.Approved

    @property
    def is_unknown(self):
        return self.level == Level.Unknown

    @property
    def is_denied(self):
        return self.level <= Level.Denied

    def load(self, details):
        self.details = details


class People(dict):

    def __init__(self):
        super(People, self).__init__()
        self._load_people()
        self.loaded = False

    def _load_people(self):
        people_dict = {}
        with open(people_path) as data_file:
            people = json.load(data_file)
        for person in people['people']:
            newbie = Person(people['people'][person])
            self[person] = newbie

    def save(self):
        people_dict = {}
        people_dict['people'] = {}
        for person in self.keys():
            if not self[person].is_unknown:
                people_dict['people'][person] = int(self[person].level)
        with open(people_path, 'w') as outfile:
            json.dump(people_dict, outfile)

    def _user_list(self, level, exact=True):
        users = {}
        for person in self.keys():
            if (self[person].level == level or
                    (self[person].level >= level and not exact)):
                users[person] = self[person]
        return users

    def find_user(self, name):
        for person in self.keys():
            if self[person].details['name'] == name:
                return self[person]
        return None

    def load(self, details):
        self.loaded = True
        if (details['id'] not in self.keys()):
            self[details['id']] = Person(Level.Unknown)
        self[details['id']].load(details)

    def admin_list(self):
        return self._user_list(Level.Admin, False)

    def approved_list(self):
        return self._user_list(Level.Approved, False)

    def unknown_list(self):
        return self._user_list(Level.Unknown)

    def denied_list(self):
        return self._user_list(Level.Denied)
