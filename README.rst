Go About Survey tool
====================

This project uses `git` and `python`.


Isolating the Python environment with virtualenv_ is recommended. Use
the  following commands to set up a development environment within the
Git workspace::

    virtualenv .
    . bin/activate
    pip install -r dev_requirements.txt

Some parts of the import need extra settings with secret information, these
can be configured using a configuration file. There are three options to
provide a configuration file

1. In `/etc/goabout/goabout-survey.conf`
2. In `~/.goabout-survey.conf`
3. By specifying a file using the `-c` cli flag

All properties are overloaded in the above order; 1) takes precedence over
defaults, 2) over properties defined in 1) and finally all properties from 3)
take precedence.

See goabout-survey.conf.example

Secrets can be found in LastPass, usually.



.. _virtualenv: http://virtualenv.org

