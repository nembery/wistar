# docker run -d --privileged -p 80:80 -v /opt/wistar/user_images:/opt/wistar/user_images -v /var/run/libvirt:/var/run/libvirt --name wistar01 juniper/wistar
FROM ubuntu:16.04

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /opt/wistar/user_images/instances && mkdir -p /opt/wistar/media && mkdir -p /opt/wistar/seeds \
    && mkdir /opt/wistar/scripts

COPY requirements.txt /opt/wistar/requirements.txt

RUN apt-get update && apt-get install -y build-essential libxml2-dev libxslt1-dev libz-dev libffi-dev \
    libssl-dev python-dev git python-pip qemu-kvm libvirt-bin socat python-pexpect python-libvirt \
    python-yaml unzip bridge-utils python-numpy genisoimage python-netaddr \
    python-markupsafe python-setuptools mtools dosfstools
RUN pip install -r /opt/wistar/requirements.txt

WORKDIR /opt/wistar
COPY app /opt/wistar/app
COPY cloud_init_templates /opt/wistar/scripts
RUN /opt/wistar/app/manage.py migrate
EXPOSE 80
ENTRYPOINT /opt/wistar/app/manage.py runserver 0.0.0.0:80