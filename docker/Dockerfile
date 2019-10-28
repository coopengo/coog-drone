FROM alpine:3.7
MAINTAINER Coopengo <support@coopengo.com>

RUN apk add --no-cache \
        bash git python3 redis graphviz libmagic \
        py3-lxml py3-psycopg2 py3-redis py3-ldap3 uwsgi-python3 \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && pip3 install \
        "fastjsonschema==2.13" \
        "flake8" \
        "pyflakes" \
        "ipaddress" \
        "dateutils" \
        "num2words" \
        "python-sql" \
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
        "zeep" \
        "PyPDF2" \
    && rm -rf /root/.cache \
    && find / -name "__pycache__" -prune -exec rm -rf {} \;

RUN git config --system url.https://github.com/.insteadOf git@github.com:
RUN mkdir /workspace/ /workspace/drone/ /workspace/drone/conf /workspace/drone/tmp
