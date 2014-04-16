#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>


import os
import json
import glob
import fabric

from fabric.api import *
from fabric.colors import green, red


def config(stage_id):
    env.config = ""


def local():
    env.host_string     = "localhost"
    env.user            = "localuser"
    env.local           = True
    cmd                 = "local command to run server"
    local(cmd)


def remote():
    env.host_string     = "remotehost"
    env.user            = "remoteuser"
    env.key_filename    = "ssh_key_path"
    env.local           = False


def init():
    if not env.local:
        run("")
    if not fabric.contrib.files.exists(env.config["path"]):
        run("git clone {stage.repository} -b {stage.branch} {stage.path}".format(**env.config))


def deploy():

    env.lcwd = os.path.dirname(__file__)

    config = env.config
    context = config["context"]

    print(red("Beginning Deploy to: {user}@{host_string}".format(**env)))

    # with cd("%s/" % env.config["path"]):
    #     run("pwd")

    #     print(green("Switching branch."))
    #     run("git checkout {branch}".format(**config))

    #     print(green("Pulling from GitHub."))
    #     run("git pull")

    #     print(green("Uploading bashrc"))
    #     fabric.contrib.files.upload_template("fab/bashrc.sh",
    #                                          "{path}/bashrc.sh".format(**config),
    #                                          context=context,
    #                                          use_jinja=True)
    #     run("sudo cp -f {path}/bashrc.sh /root/metaphor.sh".format(**config))

    #     print(green("Uploading setting.py"))
    #     fabric.contrib.files.upload_template("fab/settings.py",
    #                                          "{path}/lccsrv/settings.py".format(**config),
    #                                          context=context,
    #                                          use_jinja=True)
    #     fabric.contrib.files.upload_template("fab/paths.py",
    #                                          "{path}/lccsrv/paths.py".format(**config),
    #                                          context=context,
    #                                          use_jinja=True)

    #     print(green("Uploading usgi.ini"))
    #     fabric.contrib.files.upload_template("fab/uwsgi.ini",
    #                                          "{path}/uwsgi.ini".format(**config),
    #                                          context=context,
    #                                          use_jinja=True)
    #     run("sudo cp -f {path}/uwsgi.ini /etc/uwsgi/apps-available/{stage}.ini".format(**config))
    #     run("sudo ln -sf /etc/uwsgi/apps-available/{stage}.ini /etc/uwsgi/apps-enabled/{stage}.ini".format(**config))
    #     run("sudo /etc/init.d/uwsgi stop {stage}".format(**config))

    #     print(green("Uploading nginx config"))
    #     fabric.contrib.files.upload_template("fab/nginx.conf",
    #                                          "{path}/nginx.conf".format(**config),
    #                                          context=context,
    #                                          use_jinja=True)
    #     run("sudo cp -f {path}/nginx.conf /etc/nginx/sites-available/{stage}".format(**config))
    #     run("sudo ln -sf /etc/nginx/sites-available/{stage} /etc/nginx/sites-enabled/{stage}".format(**config))
    #     run("sudo /etc/init.d/nginx stop".format(**config))

        # print(green("Syncing database."))
        # # run("python manage.py syncdb --noinput")

        # print(green("Creating indexes."))
        # run("python manage.py syncdb --noinput --settings=lccsrv.settings")


def run_test():
    config("dev")
    deploy()
    restart()
    test()


def devdeploy():
    config("dev")
    deploy()
    restart()


def proddeploy():
    config("prod")
    deploy()
    restart()
