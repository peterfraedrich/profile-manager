#!/usr/bin/env python3

import os
import platform
import fire
import peewee
from datetime import datetime

ROOT_PATH = None
DEBUG = False
DB = peewee.SqliteDatabase(None)

# class ProfileManager provides the CLI interface for our tool
class ProfileManager:
    '''
    Profile-Manager is a small utility to manage AWS credential profiles. For those who work in environments
    with multiple AWS accounts, or do consulting that requires access to multiple unrelated accounts, having
    a simple way to manage your identities across those accounts is priceless.
    '''

    def __init__(self, debug=False):
        global DEBUG
        if debug:
            DEBUG = True
        resolve_user_path()
        check_db()
        return

    def set(self, profile):
        '''
        Sets the provided argument PROFILE as the active profile
        '''
        return profile

    def unset(self):
        '''
        Unsets all profile variables in the environment
        '''
        return 'unset'

    def ls(self):
        '''
        List all available profiles
        '''
        profiles = AWSCredential.select().namedtuples()
        print()
        print('{:20} | {:5} | {:20} | {:20} | {:1}'.format('PROFILE', 'TYPE', 'CREATED', 'LAST ACTIVE', 'ACTIVE'))
        print('{}|{}|{}|{}|{}'.format('='*21, '='*7, '='*22, '='*22, '='*7))
        for p in profiles:
            print('{:20} | {:5} | {:20} | {:20} | {:1}'.format(p.profile, p.profile_type, p.created, p.last_activated, p.is_active))
        print()
        return
    
    def add(self, profile=None, key=None, secret=None, region=None):
        '''
        Add a new profile with the provided NAME, KEY, SECRET, and REGION
        '''
        prompts = {
            'profile' : 'Please enter a profile name -> ',
            'key' : 'Please enter your AWS profile key -> ',
            'secret' : 'Please enter your AWS secret key -> ',
            'region' : 'Please enter the default region -> '
        }
        res = {
            'is_active' : False,
            'last_activated': -1
        }
        res['created'] = datetime.now()
        res['profile_type'] = "AWS"
        interactive = False
        for k,v in {'profile': profile, 'key': key, 'secret': secret, 'region': region}.items() :
            if v == None:
                res[k] = input(prompts[k])
        new = AWSCredential.create(**res)
        new.save()
        audit(res['created'], res['profile'], 'CREATE_PROFILE', 'AWS')
        return 'add'
    
    def rm(self, profile):
        '''
        Remove a profile that matches the provided PROFILE name
        '''
        return 'rm'
    
    def config(self):
        '''
        Print the current config
        '''
        return 'config'

class AWSCredential(peewee.Model):
    profile = peewee.CharField()
    profile_type = peewee.CharField()
    key = peewee.CharField()
    secret = peewee.CharField()
    region = peewee.CharField()
    created = peewee.TimestampField()
    last_activated = peewee.TimestampField()
    is_active = peewee.BooleanField()
    class Meta:
        database = DB

class Audit(peewee.Model):
    timestamp = peewee.TimestampField()
    profile = peewee.CharField()
    profile_type = peewee.CharField()
    action = peewee.CharField()
    class Meta:
        database = DB

def audit(timestamp, profile, action, type="AWS"):
    new = Audit.create(timestamp=timestamp,profile=profile, action=action, profile_type=type)
    new.save()
    return

def trace(*args, **kwargs):
    if DEBUG:
        print('TRACE: ', *args, **kwargs)

def resolve_user_path():
    '''
    depending on what platform we are on, we want to use either ~ or %userprofile% as
    our root directory; this is how we resolve that ROOT_PATH
    '''
    global ROOT_PATH
    custom_path = os.getenv('PROFILE_MANAGER_PATH', None)
    if custom_path:
        ROOT_PATH = custom_path
        trace('ROOT_PATH', ROOT_PATH)
        return
    p = {
        'Linux': '~/.profile-manager/',
        'Darwin': '~/.profile-manager/',
        'Windows': '%%userprofile%%\AppData\Local\profile-manager\\',
    }
    ROOT_PATH=p[platform.system()]
    trace('ROOT_PATH', ROOT_PATH)
    return

def check_db():
    '''
    checks to see if a database has already been init'd in the root dir and creates
    one if not
    '''
    db_path = '{}profile-manager.sqlite'.format(ROOT_PATH)
    if not os.path.exists(db_path):
        trace("db does not exist at "+db_path)
        make_db(db_path)
    DB.init(db_path, pragmas={'journal_mode':'wal'})
    DB.connect()
    return

def make_db(db_path):
    trace('generating new database at '+db_path)
    global DB
    DB.init(db_path, pragmas={'journal_mode':'wal'})
    DB.connect()
    DB.create_tables([AWSCredential, Audit])
    return


if __name__ == '__main__':
    fire.Fire(ProfileManager, name='profile-manager')