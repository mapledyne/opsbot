"""This just creates a 'Strings' object for anyone that imports this module.

To use it, import this module and then you can do:
>>> from strings import Strings
>>> print(Strings['HELP'])

Then you can just add any value to the YAML file (strings.yml) and it can be
accessed through this object.
"""
import yaml
Strings = {}

with open('opsbot/strings.yml', 'r') as stream:
    Strings = yaml.load(stream)
