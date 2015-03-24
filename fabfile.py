#!/usr/bin/env python
# coding: utf-8
# Author: Vova Zaytsev <zaytsev@usc.edu>

#
# Basic Usage:
# fab build_container:stage=prod
#

import fabric
import glob
import os
import os.path
import yaml

from jinja2 import Environment
from jinja2 import FileSystemLoader

from fabric.api import cd
from fabric.api import env
from fabric.colors import green
from fabric.colors import red
from fabric.operations import local
from fabric.operations import run
from fabric.operations import sudo

templates = Environment(loader=FileSystemLoader("./conf/templates/"))

def build_container(stage="alpha"):

    if stage == "prod":
        print(red("Building Docker container for %s" % stage))
    else:
        print(green("Building Docker container for %s" % stage))
    with open("conf/%s.yml" % stage, "r") as config_yml:
        config = yaml.load(config_yml)

    # Prepare build root
    local("rm -rf %s" % config["build"]["root"])
    local("mkdir -p  %s" % config["build"]["root"])
    local("mkdir -p  %s/conf" % config["build"]["root"])
    local("echo '*' > %s/.gitignore" % config["build"]["root"])
    for template_path in glob.glob("./conf/templates/*"):
        template_name = os.path.basename(template_path)
        template = templates.get_template(template_name)
        with open("%s/conf/%s" % (config["build"]["root"], template_name), "wb") as o_fl:
            o_fl.write(template.render(config))
    local("mv %s/conf/Dockerfile ./Dockerfile" % config["build"]["root"])
    local("echo '*' > %s/.gitignore" % config["build"]["root"])
    local("docker build .")



# def dev():
#     env.config = {
#         "repository":   "https://github.com/MediaAnalysisTools/nlcd.git",
#         "branch":       "dev",
#         "context":       json.load(open("fab/config.dev.json", "r")),
#     }
#     env.config["path"] = env.config["context"]["ROOT"]
#     env.config["logs"] = env.config["context"]["LOG_DIR"]
#     env.config["stage"] = env.config["context"]["STAGE"]


# def prod():
#     env.config = {
#         "repository":   "https://github.com/MediaAnalysisTools/nlcd.git",
#         "branch":       "prod",
#         "context":      json.load(open("fab/config.prod.json", "r")),
#     }
#     env.config["path"] = env.config["context"]["ROOT"]
#     env.config["logs"] = env.config["context"]["LOG_DIR"]
#     env.config["stage"] = env.config["context"]["STAGE"]


# def server():
#     env.host_string  = "162.243.42.148"
#     env.user         = "root"
#     env.key_filename = "~/.ssh/id_rsa"
#     env.local        = False


# def init():
#     config = env.config
#     if not env.local:

#         print(green("Installing packages."))
#         run("aptitude update")
#         run("aptitude upgrade")
#         run("aptitude -f install %s" % " ".join(UBUNTU_PACKAGES))

#         if not fabric.contrib.files.exists(env.config["path"]):
#             print(green("Clonning repository."))
#             run("git clone {repository} -b {branch} {path}".format(**env.config))
#         else:
#             print(green("Repository already exists"))

#         print(green("Installing python requirements."))
#         run("pip install -r {path}/requirements.txt".format(**config))

#         print(green("Setting up logs."))
#         run("mkdir -p {logs}".format(**config))
#         run("mkdir -p {path}/logs".format(**config))
#         run("chown root:root -R {logs}".format(**config))
#         run("chown root:root -R {path}".format(**config))


# def update_ubuntu():
#     with open("ubuntu.txt", "r") as i_fl:
#         ubuntu_packages = i_fl.read().split("\n")
#     sudo("aptitude update")
#     sudo("aptitude install %s" % " ".join(ubuntu_packages))


# def deploy():

#     env.lcwd = os.path.dirname(__file__)
#     config = env.config

#     context = config["context"]

#     print(red("Beginning Deploy to: {user}@{host_string}".format(**env)))

#     with cd("%s/" % env.config["path"]):
#         run("pwd")

#         print(green("Switching branch."))
#         run("git reset --hard".format(**config))
#         run("git checkout {branch}".format(**config))

#         print(green("Pulling from GitHub."))
#         run("git pull")

#         print(green("Fetching requirements."))
#         run("pip install -r {path}/requirements.txt".format(**config))

#         print(green("Setting up logs."))
#         run("mkdir -p {logs}".format(**config))
#         run("mkdir -p {path}/logs".format(**config))
#         run("chown root:root -R {logs}".format(**config))
#         run("chown root:root -R {path}".format(**config))


#         print(green("Uploading setting.py"))
#         fabric.contrib.files.upload_template("fab/settings.py",
#                                              "{path}/nlcd/settings.py".format(**config),
#                                              context=context,
#                                              use_jinja=True)

#         print(green("Uploading usgi.ini"))
#         fabric.contrib.files.upload_template("fab/uwsgi.ini",
#                                              "{path}/uwsgi.ini".format(**config),
#                                              context=context,
#                                              use_jinja=True)
#         run("cp -f {path}/uwsgi.ini /etc/uwsgi/apps-available/{stage}.ini".format(**config))
#         run("ln -sf /etc/uwsgi/apps-available/{stage}.ini /etc/uwsgi/apps-enabled/{stage}.ini".format(**config))
#         run("/etc/init.d/uwsgi restart {stage}".format(**config))

#         print(green("Uploading nginx config"))
#         fabric.contrib.files.upload_template("fab/nginx-site.conf",
#                                              "{path}/nginx-site.conf".format(**config),
#                                              context=context,
#                                              use_jinja=True)
#         fabric.contrib.files.upload_template("fab/nginx.conf",
#                                              "{path}/nginx.conf".format(**config),
#                                              context=context,
#                                              use_jinja=True)
#         run("cp -f {path}/nginx.conf /etc/nginx/nginx.conf".format(**config))
#         run("cp -f {path}/nginx-site.conf /etc/nginx/sites-available/{stage}".format(**config))
#         run("ln -sf /etc/nginx/sites-available/{stage} /etc/nginx/sites-enabled/{stage}".format(**config))
#         run("rm -f /etc/nginx/sites-available/default".format(**config))
#         run("rm -f /etc/nginx/sites-enabled/default".format(**config))
#         run("sudo service nginx restart".format(**config))


# def build_assets():

#     env.lcwd = os.path.dirname(__file__)
#     config = env.config

#     context = config["context"]

#     with open("assets.json", "rb") as i_fl:
#         assets = json.load(i_fl)

#     with cd("%s/" % env.config["path"]):
#         print(green("Building assets."))
#         build = {}
#         build_in_out = {}
#         timestamp = calendar.timegm(time.gmtime())
#         dir_name = "build/%s" % timestamp
#         local("mkdir -p %s" % dir_name)
#         for key, files in assets.iteritems():
#             uid = uuid.uuid4().hex
#             ext = "js" if key.startswith("JS") else "css"
#             fl_name = "%s/%s.%s" % (dir_name, uid, ext)
#             local("touch %s" % fl_name)
#             for i_fl in files:
#                 local("cat < %s >> %s" % (i_fl, fl_name))
#                 local("echo '\\n' >> %s" % fl_name)
#             o_file = "%s/%s.min.%s" % (dir_name, uid, ext)
#             if ext == "js":
#                 local("java -jar compiler.jar --language_in=ECMASCRIPT5 --js_output_file=%s %s" % (o_file, fl_name))
#             if ext == "css":
#                 local("java -jar compressor.jar %s -o %s" % (fl_name, o_file))

#             build_in = o_file
#             build_out = "webapp/assets/%s/%s.min.%s" % (timestamp, uid, ext)

#             build[key] = build_out
#             build_in_out[key] = (build_in, build_out)

#     run(("mkdir -p {path}/webapp/assets/%s" % timestamp).format(**config))
#     fabric.contrib.files.upload_template("webapp/templates/app.tpl.html",
#                                          "{path}/webapp/templates/app.html".format(**config),
#                                          context=build,
#                                          use_jinja=True)
#     for f_in, f_out in build_in_out.values():
#         fabric.contrib.files.upload_template(f_in, ("{path}/%s" % f_out).format(**config))




# def devdeploy():
#     dev()
#     server()
#     deploy()


# def proddeploy():
#     prod()
#     server()
#     deploy()
