FROM ubuntu:14.10

# Install required packages
RUN add-apt-repository -y ppa:nginx/stable
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y build-essential git
RUN apt-get install -y nginx
RUN apt-get install -y python
RUN apt-get install -y python-dev
RUN apt-get install -y python-numpy
RUN apt-get install -y python-scipy
RUN apt-get install -y python-matplotlib
RUN apt-get install -y libleveldb1
RUN apt-get install -y libleveldb-dev
RUN apt-get install -y python-lxml
RUN apt-get install -y uwsgi
RUN apt-get install -y uwsgi-plugin-python
RUN apt-get install -y supervisor

# Create root directory
ADD {{build.root}} {{deploy.root}}

# Clone repository & install dependences
RUN git clone {{deploy.repository}} {{deploy.branch}} {{deploy.path}}
# RUN pip install -r {{deploy.path}}/requirements.txt

# RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf

# ADD /site.conf /etc/nginx/sites-available/lucid

# VOLUME ["/lucid_app"]

# EXPOSE 80

# CMD ["nginx"]
