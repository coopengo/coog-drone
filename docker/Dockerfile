FROM alpine:3.8
MAINTAINER Coopengo <support@coopengo.com>

RUN apk add --no-cache \
        bash git python3 redis graphviz libmagic \
        py3-lxml py3-psycopg2 py3-redis py3-ldap3 uwsgi-python3 \
        gcc musl-dev python3-dev libffi-dev libressl-dev \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && pip3 install \
        "fastjsonschema" \
        "flake8" \
        "pyflakes" \
        "ebcdic" \
        "ipaddress" \
        "dateutils" \
        "num2words" \
        "python-sql==1.1.0" \
        "polib" \
        "Genshi" \
        "relatorio" \
        "python-magic" \
        "pydot" \
        "pyparsing" \
        "python-stdnum" \
        "unidecode" \
        "intervaltree" \
        "filelock" \
        "wrapt" \
        "werkzeug<0.15" \
        "simpleeval" \
        "ldap3" \
        "requests" \
        "raven" \
        "redis<3" \
        "msgpack-python" \
        "celery" \
        "rq" \
        "mock" \
        "phonenumbers" \
        "passlib" \
        "pyjwt" \
        "requests-mock" \
        "validate_email" \
        "xmlrunner" \
        "zeep" \
        "PyPDF2" \
        "cryptography" \
    && rm -rf /root/.cache \
    && find / -name "__pycache__" -prune -exec rm -rf {} \;

RUN git config --system url.https://github.com/.insteadOf git@github.com:
RUN mkdir /workspace/ /workspace/drone/ /workspace/drone/conf /workspace/drone/tmp
