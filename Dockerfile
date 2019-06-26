FROM alpine:3.10

# These are always installed. Notes:
#   * dumb-init: a proper init system for containers, to reap zombie children
#   * bash: For entrypoint, and debugging
#   * ca-certificates: for SSL verification during Pip and easy_install
#   * python: the binaries themselves
ENV PACKAGES="\
  bash \
  ca-certificates \
  python3 \
  git \
  openssh \
  " PYTHONUNBUFFERED=1

# Copy in the entrypoint script -- this installs prerequisites on container start.
COPY pipeline.py prepare-creds.py /

RUN echo "**** install Python ****" && \
  apk add --no-cache $PACKAGES && \
  if [ ! -e /usr/bin/python ]; then ln -sf python3 /usr/bin/python ; fi \
  \
  && if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python3 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python-config3 /usr/bin/python-config; fi \
  && \
  echo "**** install pip ****" && \
  python3 -m ensurepip && \
  rm -r /usr/lib/python*/ensurepip && \
  pip3 install --no-cache --upgrade pip setuptools wheel && \
  if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi \
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
  && mv /pipeline.py /nu-ecsplatform/