FROM alpine:3.7

RUN apk add --no-cache\
    git \
    python2 \
    postgresql \
    py2-pip \
    py2-lxml \
    py2-psycopg2 \
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
        \
    && pip install \
        requests \
        werkzeug \
        wrapt \
        "ldap3<2.0" \
        pyflakes \
        dateutils \
        num2words \
        python-sql \
        polib \
        Genshi \
        relatorio \
        pydot \
        pyparsing \
        python-stdnum \
        unidecode \
        intervaltree \
        filelock \
        simpleeval \
        rq \
        redis \
        hiredis \
        msgpack-python \
        argcomplete \
        Mock \
        chardet \
        vobject \
        pytest \
        flake8 \
    && apk del .build-deps

RUN git config --system url.https://github.com/.insteadOf git@github.com:
RUN mkdir /workspace/ /workspace/drone/ /workspace/drone/conf /workspace/drone/tmp
