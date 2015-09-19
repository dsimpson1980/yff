import yaml
import os

default_data = os.path.expanduser('~/YahooFF/data.yaml')

def get_yaml_data(filename=default_data, *args):
    with open(filename, 'r') as f:
        y = yaml.load(f)
    return tuple([y.get(arg, None)
                  for arg in args]) if len(args) > 1 else y[args[0]]


def get_consumer_secret(filename=default_data):
    return get_yaml_data(filename, 'consumer', 'secret')


def get_league_number(filename=default_data):
    return get_yaml_data(filename, 'league_number')


def get_league_key(filename=default_data):
    data = get_yaml_data(filename, 'league', 'league_number')
    return '%s.l.%s' % data

def get_yahoo_username(filename=default_data):
    return get_yaml_data(filename, 'yahoo_username')
