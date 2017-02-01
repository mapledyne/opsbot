import json

people_path = '/opt/opsbot/people.json'

ADMIN = 50
UNKNOWN = 0
DENIED = -10
APPROVED = 10


class Person:
    def __init__(self, level):
        self.level = level
        self.details = {}

    @property
    def loaded(self):
        return len(self.details) > 0

    @property
    def is_admin(self):
        return self.level >= ADMIN

    @property
    def is_approved(self):
        return self.level >= APPROVED

    @property
    def is_unknown(self):
        return self.level == UNKNOWN

    @property
    def is_denied(self):
        return self.level <= DENIED

    def load(details):
        self.details = details


class People(dict):

    def __init__(self):
        super(People, self).__init__()
        self._load_people()

    def _load_people(self):
        people_dict = {}
        with open(people_path) as data_file:
            people = json.load(data_file)
        for person in people['people']:
            newbie = Person(people['people'][person])
            self[person] = newbie

    def _user_list(self, level, exact=True):
        users = {}
        for person in self.keys():
            if (self[person].level == level or
                    (self[person].level >= level and not exact)):
                users[person] = self[person]
        return users

    def admin_list(self):
        return self._user_list(ADMIN, False)

    def approved_list(self):
        return self._user_list(APPROVED, False)

    def unknown_list(self):
        return self._user_list(UNKNOWN)

    def denied_list(self):
        return self._user_list(DENIED)
