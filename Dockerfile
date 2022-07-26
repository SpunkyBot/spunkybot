# $ docker build -t spunkybot .
# $ docker run -it --rm --name spunkybot spunkybot

FROM python:2
MAINTAINER "Alexander Kress <feedback@spunkybot.de>"
WORKDIR /usr/src/app
VOLUME [ ".", "/usr/src/app" ]
CMD [ "python", "./spunky.py" ]
