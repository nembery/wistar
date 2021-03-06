# docker run -d --privileged -p 80:80 -v /opt/wistar/user_images:/opt/wistar/user_images -v /var/run/libvirt:/var/run/libvirt --name wistar01 juniper/wistar
FROM python:3.9-slim

RUN mkdir -p /opt/wistar/user_images/instances && mkdir -p /opt/wistar/media && mkdir -p /opt/wistar/seeds \
    && mkdir /opt/wistar/scripts

COPY requirements.txt /opt/wistar/requirements.txt

RUN pip install -r /opt/wistar/requirements.txt

WORKDIR /opt/wistar
COPY app /opt/wistar/app
COPY cloud_init_templates /opt/wistar/scripts
RUN /opt/wistar/app/manage.py migrate
EXPOSE 80
ENTRYPOINT /opt/wistar/app/manage.py runserver 0.0.0.0:80