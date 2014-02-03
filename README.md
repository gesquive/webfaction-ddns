webfaction-ddns
====================

A script to update Webfaction DNS entries

Steps to install:

1. Copy somewhere accessible
2. Secure the config file
2. [optional] If you want logging, create the directory /var/log/webfaction-ddns
3. Add entry to cron

----
For example:
Download and copy the script to your home directory and make it executable
```
wget https://raw.github.com/gesquive/webfaction-ddns/master/webfaction-ddns.py ~
chmod +x webfaction-ddns.py
```

Run script once as the <user> that will run it regularly. This will create the
config file in `~/.config/webfaction-ddns/webfaction-ddns.conf.`
Since your password is plain text in this config, secure the file.
```
chmod 600 ~/.config/webfaction-ddns/webfaction-ddns.conf
```

[optional] Create the logging directory and make it writable

```
sudo mkdir /var/log/webfaction-ddns/
sudo chown <user>:<user> /var/log/webfaction-ddns
```

Add entry to cron, for example, to run every hour:
```
0 * * * * /usr/bin/python ~/webfaction-ddns.py
```

