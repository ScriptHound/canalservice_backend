FROM python:3.8-slim

WORKDIR /canalservice

RUN apt-get -y update --fix-missing
RUN apt-get -y install apt-utils
RUN apt-get -y dist-upgrade
RUN apt-get -y install tmux gcc

RUN apt-get -y clean
COPY . /canalservice

RUN pip3 install -r requirements.txt

ENTRYPOINT ["sh", "docker-entrypoint.sh"]