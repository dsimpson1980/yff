import ConfigParser
import os
import errno

config = ConfigParser.ConfigParser()
default = os.path.expanduser('~/YahooFF/config')

def set_default_config():
    mkdir_p('~/YahooFF')
    parameters = dict(Yff=['consumer', 'secret'],
                      Fantasy=['league', 'league_number'],
                      Yahoo=['username'])
    for section, keys in parameters.iteritems():
        config.add_section(section)
        for key in keys:
            config.set(section, key)
    with open(default, 'w') as file:
        config.write(file)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def config_map(section, key):
    try:
        value = config.get(section, key)
        if value == '':
            value = raw_input('Enter %s %s:' % (section, key))
            config.set(section, key, value)
        with open(default, 'w') as f:
            config.write(f)
    except ConfigParser.NoOptionError:
        value = None
    return value

def get_yahoo_username(query=None):
    username = config_map('Yahoo', 'username')
    if username == '':
        if query is None:
            username = raw_input('Enter %s' % 'username')
        else:
            username = query()
    return username

def get_consumer_secret(query=None):
    consumer = config_map('Yff', 'consumer')
    secret = config_map('Yff', 'secret')
    if '' in [consumer, secret]:
        if query is None:
            consumer = raw_input('Enter %s:' % 'consumer')
            secret = raw_input('Enter %s:' % 'secret')
        else:
            consumer, secret = query()
    return consumer, secret

if os.path.exists(default):
    config.read(default)
else:
    set_default_config()
