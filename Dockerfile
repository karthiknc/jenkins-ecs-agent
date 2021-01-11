FROM node:14.15.4-buster-slim

ENV PYTHONUNBUFFERED=1

COPY pipeline.py prepare-creds.py /

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  libgtk2.0-0 \
  libgtk-3-0 \
  libnotify-dev \
  libgconf-2-4 \
  libnss3 \
  libxss1 \
  libasound2 \
  libxtst6 \
  xauth \
  xvfb \
  python3-pip \
  ca-certificates \
  git \
  ssh \
  && npm install -g cypress --unsafe-perm \
  \
  && if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi \
  \
  && if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python3 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python-config3 /usr/bin/python-config; fi \
  \
  && pip3 install --no-cache --upgrade setuptools wheel \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi \
  && pip install boto3 \
  && mkdir ~/.aws \
  && touch ~/.aws/config \
  && echo '[default]' >> ~/.aws/config \
  && echo 'region = eu-west-1' >> ~/.aws/config \
  && echo 'output = json' >> ~/.aws/config \
  && mkdir ~/.ssh \
  && touch ~/.ssh/known_hosts \
  && ssh-keyscan github.com >> ~/.ssh/known_hosts \
  && mkdir /nu-ecsplatform \
  && mv /pipeline.py /nu-ecsplatform/ \
  && rm -rf /var/lib/apt/lists/*
