import yaml

__author__ = 'davidsimpson'

default_data = 'etc/data.yaml'

def get_yaml_data(filename=default_data, *args):
    with open(filename, 'r') as f:
        y = yaml.load(f)
    return tuple([y[arg] for arg in args]) if len(args) > 1 else y[args[0]]


def get_consumer_secret(filename=default_data):
    return get_yaml_data(filename, 'consumer', 'secret')


def get_league_number(filename=default_data):
    return get_yaml_data(filename, 'league_number')


def get_league_key(filename=default_data):
    data = get_yaml_data(filename, 'league', 'league_number')
    return '%s.l.%s' % data
