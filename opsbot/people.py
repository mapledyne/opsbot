"""People (and Person) objects to wrap info about a user."""
from enum import IntEnum
import json
import os

import config

people_path = config.DATA_PATH + 'people.json'


class Level(IntEnum):
    """The levels a person can be."""

    Admin = 50
    Expired = 5
    Unknown = 0
    Denied = -10
    Approved = 10


class Person(object):
    """One person and their associated info."""

    def __init__(self, id, level):
        """Set up a user = all we need is their level at this point."""
        self.level = Level(level)
        self.id = id
        self.details = {}

    @property
    def loaded(self):
        """Return true if the user has been loaded with slack details."""
        return len(self.details) > 0

    @property
    def is_admin(self):
        """Return true if the user is an admin."""
        return self.level == Level.Admin

    @property
    def is_approved(self):
        """Return true if the user is approved to request access.

        Note: This returns true if the user is Level.Approved, *or*
        Level.Admin. Don't use this to test explicit users. Use it to
        test if the user is able to request production access.
        """
        return self.level >= Level.Approved

    @property
    def is_unknown(self):
        """Return true if there is no record of this user."""
        return self.level == Level.Unknown

    @property
    def is_denied(self):
        """Return true if the user has been denied."""
        return self.level <= Level.Denied

    def load(self, details):
        """Load slack details into the user."""
        self.details = details

    @property
    def name(self):
        """Return the name of the user."""
        if 'name' not in self.details:
            return self.id
        return self.details['name']


class People(dict):
    """Collection of people that the system knows about.

    The key for the dict is the user's slack id (not their name, so
    something that looks like: 'U0ULENHK9'). Use find_user() to find
    someone by their name instead of their id.
    """

    def __init__(self):
        """Create the basic object."""
        super(People, self).__init__()
        self._load_people()
        self.loaded = False

    def _load_people(self):
        """Load people and details from our saved JSON file."""
        if not os.path.isfile(people_path):
            return
        with open(people_path) as data_file:
            people = json.load(data_file)
        for person in people['people']:
            newbie = Person(person, people['people'][person])
            self[person] = newbie

    def save(self):
        """Save our details to the JSON file."""
        people_dict = {}
        people_dict['people'] = {}
        for person in self.keys():
            if not self[person].is_unknown:
                people_dict['people'][person] = int(self[person].level)
        with open(people_path, 'w') as outfile:
            json.dump(people_dict, outfile)

    def _user_list(self, level, exact=True):
        """Return a list of users that match a given level.

        This is intended to be used by functions like admin_list() and similar.

        Args:
            level (Level or int): Level of users to return.
            exact (boolean): If False, return anyone of level or above.
                (useful for approved_list() in particular since we want anyone
                 at 'approved' or higher)
        """
        users = {}
        for person in self.keys():
            if (self[person].level == level or
                    (self[person].level >= level and not exact)):
                users[person] = self[person]
        return users

    def find_user(self, name):
        """Return a user with the specified name."""
        for person in self.keys():
            if self[person].details['name'] == name:
                return self[person]
        return None

    def load(self, details):
        """Load slack JSON details for a user."""
        self.loaded = True
        if (details['id'] not in self.keys()):
            self[details['id']] = Person(details['id'], Level.Unknown)
        self[details['id']].load(details)

    @property
    def admin_list(self):
        """Return a list of users with Level.Admin."""
        return self._user_list(Level.Admin, False)

    @property
    def approved_list(self):
        """Return all users who are approved to request access."""
        return self._user_list(Level.Approved, False)

    @property
    def unknown_list(self):
        """Return a list of users that are unknown to the system.

        Note: This typically can return a very long list: everyone in the
        slack org that isn't another status.
        """
        return self._user_list(Level.Unknown)

    @property
    def denied_list(self):
        """Return a list of users that have been denied access."""
        return self._user_list(Level.Denied)
