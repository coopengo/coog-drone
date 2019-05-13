FROM alpine:3.7
MAINTAINER Coopengo <support@coopengo.com>

RUN apk add --no-cache\
    git \
    python2 \
    postgresql \
    py2-pip \
    py2-lxml \
    py2-psycopg2 \
    libmagic \
    ack

RUN apk add --no-cache --virtual .build-deps \
        wget \
        ca-certificates \
        make \
        gcc \
        g++ \
        linux-headers \
        musl-dev \
        python2-dev \
        libmagic \
        \
    && pip install \
        "celery[redis]==4.1.1" \
        "dateutils==0.6.6" \
        "filelock==2.0.12" \
        "Genshi==0.7" \
        "hiredis==0.2.0" \
        "intervaltree==2.1.0" \
        "ldap3==2.5.1" \
        "lxml==3.8.0"\
        "mock==2.0.0" \
        "msgpack-python==0.4.8" \
        "num2words==0.5.5" \
        "polib==1.0.8" \
        "psycopg2==2.7.3.1"
        "pydot==1.2.3" \
        "pyflakes==1.6.0" \
        "pyparsing==2.2.0" \
        "python-magic==0.4.15" \
        "python-sql==0.9" \
        "python-stdnum==1.6" \
        "raven==6.1.0"\
        "relatorio==0.8.1" \
        "requests==2.18.4" \
        "rq==0.13" \
        "simpleeval==0.9.5" \
        "unidecode==0.4.21" \
        "uwsgi==2.0.15"\
        "werkzeug==0.12.2" \
        "wrapt==1.10.11" \
    && apk del .build-deps

RUN git config --system url.https://github.com/.insteadOf git@github.com:
RUN mkdir /workspace/ /workspace/drone/ /workspace/drone/conf /workspace/drone/tmp
