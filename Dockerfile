FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV PATH="${PATH}:/root/.poetry/bin"
ENV WORKDIR="/app"

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing \
    apt-utils \
    apt-transport-https \
    build-essential \
    cron
#Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# Nicer Bash Setup
RUN sed -i "s/# export LS_OPTIONS/export LS_OPTIONS/" /root/.bashrc
RUN sed -i "s/# alias ll/alias ll/" /root/.bashrc
RUN sed -i "s/# alias ls/alias ls/" /root/.bashrc
RUN sed -i "s/# alias l/alias l/" /root/.bashrc

# App
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

# Install poetry packages before copying entire directory to take advantage of docker layer caching
COPY ./poetry.lock ${WORKDIR}/poetry.lock
COPY ./pyproject.toml ${WORKDIR}/pyproject.toml

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

COPY . ${WORKDIR}

CMD /bin/bash
