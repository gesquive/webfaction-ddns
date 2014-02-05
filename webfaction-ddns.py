#!/usr/bin/env python
# webfaction-ddns.py
# GusE 2014.02.02 V0.1
"""
Update WebFaction DNS entry
Uses the WebFaction DNS API
http://docs.webfaction.com/xmlrpc-api/apiref.html#dns
"""

import getopt
import sys
import os
import subprocess
import traceback
import logging
import logging.handlers

import ConfigParser
import xmlrpclib
import urllib2
import re


__app__ = os.path.basename(__file__)
__author__ = "Gus E"
__copyright__ = "Copyright 2014"
__credits__ = ["Gus E"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Gus E"
__email__ = "gesquive@gmail"
__status__ = "Beta"


#--------------------------------------
# Configurable Constants
LOG_FILE = '/var/log/webfaction-ddns/' + os.path.splitext(__app__)[0] + '.log'
LOG_SIZE = 1024*1024*200

IP_CHECK_LIST = {
                    'http://icanhazip.com',
                    'http://ip.catnapgames.com',
                    'http://ip.ryansanden.com'
                }

verbose = False
debug = False

logger = logging.getLogger(__app__)

def usage():
    usage = \
"""Usage: %s [options] forced_arg
    Update WebFaction DNS entry
Options and arguments:
  -h --help                         Prints this message.
  -v --verbose                      Writes all messages to console.
  -f --force-update                 Force an update regardless of the
                                        update history.
  -c --config <config_path>         The config to use.
                                        (default: ~/.config/webfaction-ddns.cfg)

    v%s
""" % (__app__, __version__)

    print usage


def main():
    global verbose, debug

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvc:f", \
        ["help", "verbose", "debug", "config=", "force-update"])
    except getopt.GetoptError, err:
        print str(err)
        print usage()
        sys.exit(2)

    verbose = False
    debug = False

    webfaction_username = None
    webfaction_password = None
    webfaction_domain = None
    last_ip = None
    config_path = get_config_path()
    force_update = False


    for o, a in opts:
        if o in ("-c", "--config"):
            if os.path.exists(a) and os.path.isfile(a):
                config_path = a
            else:
                print "Error: cannot access '%s'" % a
                sys.exit()

    config = ConfigParser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)

        webfaction_username = config.get("Account", "UserName").strip()
        webfaction_password = config.get("Account", "Password").strip()
        webfaction_domain = config.get("Account", "Domain").strip()
        try:
            last_ip = config.get("Local", "IP").strip()
        except:
            pass
    else:
        print "No config file exists, please fill in the following values."
        try:
            webfaction_username = raw_input("UserName: ").strip()
            webfaction_password = raw_input("Password: ").strip()
            webfaction_domain = raw_input("Domain: ").strip()
        except (KeyboardInterrupt, SystemExit):
            sys.exit()

        dir_path = os.path.dirname(config_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        config.add_section("Account")
        config.set("Account", 'UserName', webfaction_username)
        config.set("Account", 'Password', webfaction_password)
        config.set("Account", 'Domain', webfaction_domain)
        with open(config_path, 'wb') as configfile:
            config.write(configfile)

    for o, a in opts:
        if o in ("-h", "--help"):
            # Print out help and exit
            usage()
            sys.exit()
        elif o in ("-d", "--debug"):
            debug = True
        elif o in ("-v", "--verbose"):
            verbose = True
        elif o in ("-f", "--force"):
            force_update = True

    log_file = LOG_FILE
    dir_path = os.path.dirname(log_file)
    # if not os.path.exists(dir_path):
    #     os.makedirs(dir_path)
    if os.access(log_file, os.W_OK):
        file_handler = logging.handlers.RotatingFileHandler(log_file,
                                                maxBytes=LOG_SIZE, backupCount=9)
        file_formater = logging.Formatter('%(asctime)s,%(levelname)s,%(thread)d,%(message)s')
        file_handler.setFormatter(file_formater)
        logger.addHandler(file_handler)

    if verbose:
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter("[%(asctime)s] %(levelname)-5.5s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)

    try:
        current_ip = get_ip_address()
        if force_update:
            logger.info("Update forced from the command line")
            update_dns(webfaction_username, webfaction_password,
                webfaction_domain, config_path, current_ip)
            update_config(config_path, config, current_ip)
        elif last_ip != current_ip:
            logger.info("IP Changed from '%s' to '%s' updating DNS" %
                (last_ip, current_ip))
            update_dns(webfaction_username, webfaction_password,
                webfaction_domain, config_path, current_ip)
            update_config(config_path, config, current_ip)
        else:
            logger.info("No changes.")
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception, e:
        print traceback.format_exc()


def get_config_path():
    '''
    Gets the config location based on the XDG Base Directory Specification.
    If no config is found, the home directory path is returned.
    '''
    config_path = None
    project_name = __app__.split('.')[0]
    project_name = "webfaction-ddns"
    config_name = project_name+".conf"
    locations = [
    os.path.join(os.curdir, config_name),
    os.path.join(os.path.expanduser('~'), '.config', project_name, config_name),
    os.path.join('/etc', project_name, config_name),
    os.environ.get(project_name+"_CONF"),
    ]
    for path in locations:
        if path != None and os.path.exists(path) and os.path.isfile(path):
            return path
    return locations[1]


def update_config(config_path, config, current_ip):
    # config = ConfigParser.ConfigParser()
    # config.add_section("Account")
    # config.set("Account", 'UserName', webfaction_username)
    # config.set("Account", 'Password', webfaction_password)
    # config.set("Account", 'Domain', webfaction_domain)
    config.add_section("Local")
    config.set("Local", 'IP', current_ip)
    with open(config_path, 'wb') as configfile:
        config.write(configfile)


def update_dns(webfaction_username, webfaction_password,
                webfaction_domain, config_path, current_ip):
    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    (session_id, account) = server.login(webfaction_username, webfaction_password)

    home_override = None
    for override in server.list_dns_overrides(session_id):
        if override['domain'] == webfaction_domain:
            home_override = override
            break

    if home_override and home_override['a_ip'] == current_ip:
        logger.info("Remote DNS entry matches, no update needed")
        return

    if home_override:
        server.delete_dns_override(session_id, webfaction_domain, home_override['a_ip'])

    server.create_dns_override(session_id, webfaction_domain, current_ip)
    logger.info("Successfully updated webfaction server")



def get_ip_address():
    for site in IP_CHECK_LIST:
        try:
            content = urllib2.urlopen(site).read()
            grab = re.findall('\d{2,3}.\d{2,3}.\d{2,3}.\d{2,3}',
                content)
            return grab[0]
        except urllib2.URLError:
            continue

    logger.error("Can't reach any IP checking site.")
    logger.debug("Are you sure you have internet access?")
    return None


if __name__ == '__main__':
    main()
