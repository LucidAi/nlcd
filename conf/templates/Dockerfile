FROM ubuntu:14.10

# Install required packages
RUN apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:nginx/stable
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential git
RUN apt-get install -y nginx
RUN apt-get install -y python
RUN apt-get install -y python-dev
RUN apt-get install -y python-pip
RUN apt-get install -y python-numpy
RUN apt-get install -y python-scipy
RUN apt-get install -y python-oauth2
RUN apt-get install -y libleveldb1
RUN apt-get install -y libleveldb-dev
RUN apt-get install -y python-lxml
RUN apt-get install -y uwsgi
RUN apt-get install -y uwsgi-plugin-python
RUN apt-get install -y supervisor

# Create root directory
ADD {{build.root}} {{deploy.root}}

# Clone repository & install dependences
RUN git clone -b {{deploy.branch}} {{deploy.repository}} {{deploy.path}}
RUN rm {{deploy.path}}/.git
RUN pip install -r {{deploy.path}}/requirements.txt

# Create log root
RUN mkdir {{webapp.logdir}}

# Add nginx configs
RUN rm /etc/nginx/sites-enabled/default
RUN rm /etc/nginx/sites-available/default
ADD {{build.root}}/conf/nginx.conf /etc/nginx/nginx.conf
ADD {{build.root}}/conf/nginx-site.conf /etc/nginx/sites-available/lucid.conf
ADD {{build.root}}/conf/nginx-site.conf /etc/nginx/sites-enabled/lucid.conf

# Add UWSGI configs
ADD {{build.root}}/conf/uwsgi.ini /etc/uwsgi/apps-available/lucid.ini
ADD {{build.root}}/conf/uwsgi.ini /etc/uwsgi/apps-enabled/lucid.ini

# Add lucid app configs
ADD {{build.root}}/conf/settings.py {{deploy.path}}/nlcd/settings.py

EXPOSE 80
EXPOSE 443

CMD ["{{deploy.path}}/run-docker.sh"]
