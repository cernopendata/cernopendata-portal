# -*- coding: utf-8 -*-
#
# This file is part of CERN Open Data Portal.
# Copyright (C) 2015, 2016, 2017, 2018, 2020, 2021, 2023, 2024, 2026 CERN.
#
# CERN Open Data Portal is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Open Data Portal is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Open Data Portal; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

# Use Invenio's Debian image with Python-3.14
ARG BUILDPLATFORM=linux/amd64

# Debian ships the gfal2 Python bindings only for its own interpreter
# (/usr/lib/python3/dist-packages/gfal2.cpython-313-*.so, and the package
# even declares "Depends: python3 (<< 3.14)"), so they are not importable by
# this image's Python 3.14 in /usr/local. Boost.Python has the same problem:
# both libboost-python1.83 and libboost-python1.88 ship libboost_python313.so
# only. Build both against 3.14 in a throwaway stage.
#
# NOTE: this stage compiles native code that is copied into the final image,
# so both stages must resolve to the same platform. They both use
# $BUILDPLATFORM; if one is ever switched to $TARGETPLATFORM the copied
# libraries would be built for the wrong architecture.
ARG BOOST_VERSION=1.88.0
ARG GFAL2_PYTHON_VERSION=1.13.0

FROM --platform=$BUILDPLATFORM registry.cern.ch/inveniosoftware/debian:3.14 AS gfal2-builder

ARG BOOST_VERSION
ARG GFAL2_PYTHON_VERSION

# This stage is discarded; only the built libraries are copied out.
# hadolint ignore=DL3002
USER root
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        cmake \
        libgfal2-dev \
        libglib2.0-dev && \
    rm -rf /var/lib/apt/lists/*

# Build Boost.Python against Python 3.14 (only the python library is needed)
WORKDIR /build
# hadolint ignore=DL3003
RUN BOOST_ARCHIVE="boost_${BOOST_VERSION//./_}" && \
    curl -fsSL -o boost.tar.gz \
        "https://archives.boost.io/release/${BOOST_VERSION}/source/${BOOST_ARCHIVE}.tar.gz" && \
    tar xzf boost.tar.gz && \
    cd "${BOOST_ARCHIVE}" && \
    ./bootstrap.sh --with-libraries=python --with-python=/usr/local/bin/python3.14 && \
    ./b2 --with-python python=3.14 -j"$(nproc)" install && \
    ldconfig

# Build the gfal2 Python bindings against Python 3.14
WORKDIR /build/gfal2-python
RUN curl -fsSL -o gfal2-python.tar.gz \
        "https://files.pythonhosted.org/packages/source/g/gfal2-python/gfal2-python-${GFAL2_PYTHON_VERSION}.tar.gz" && \
    tar xzf gfal2-python.tar.gz --strip-components=1 && \
    cmake -B build \
        -DSKIP_TESTS=ON \
        -DCMAKE_PREFIX_PATH=/usr/local \
        -DPython_EXECUTABLE=/usr/local/bin/python3.14 && \
    cmake --build build -j"$(nproc)" && \
    cp "$(find build -name 'gfal2*.so' | head -1)" /build/gfal2.so


FROM --platform=$BUILDPLATFORM registry.cern.ch/inveniosoftware/debian:3.14

# Use XRootD 5.9.9. Only the pip wheel is used: Debian's python3-xrootd is
# built for the distro interpreter and cannot be imported by Python 3.14.
ENV XROOTD_VERSION=5.9.9

USER root

# Install CERN Open Data Portal web node pre-requisites.
#
# igtf-policy-classic replaces the EGI/IGTF yum repository and the
# ca_CERN-Root-2 RPM: it installs CERN-Root-2.pem and CERN-GridCA.pem under
# /etc/grid-security/certificates. ca-certificates, build-essential, curl,
# git and libssl-dev are already provided by the base image.
#
# swig is needed to build M2Crypto (pulled in by fts3) from its sdist, and
# libpcre2-dev to build uWSGI with regex routing support.
#
# gfal2-util-scripts provides the gfal-* command line tools; on Debian these
# are split out of python3-gfal2-util, which ships only a library for the
# distro's own interpreter. Those wrappers probe `python`/`python3` on PATH
# for an interpreter that can import both gfal2 and gfal2_util; since PATH
# leads with the virtualenv (which has gfal2 but not gfal2_util) they would
# fall through to a non-existent /usr/bin/python, so point them at Debian's
# interpreter explicitly. This only affects the gfal-* CLI, not the app.
ENV GFAL_PYTHONBIN=/usr/bin/python3
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        gfal2-plugin-http \
        gfal2-util-scripts \
        igtf-policy-classic \
        jq \
        libpcre2-dev \
        rlwrap \
        swig \
        uuid-dev \
        vim \
        voms-clients && \
    rm -rf /var/lib/apt/lists/*

# Boost.Python 3.14 runtime, built in the gfal2-builder stage above
COPY --from=gfal2-builder /usr/local/lib/libboost_python314.so* /usr/local/lib/

# node-sass is deliberately absent: invenio-assets declares sass (dart-sass)
# in its own webpack package.json, and node-sass 6 cannot build on Node 24.
# The `ln` makes a relative link, so that if the directory is copied, it
# still works. Change group to root to support OpenShift runtime.
RUN ldconfig && \
    npm install -g clean-css@3.4.24 requirejs@2.3.6 uglify-js@3.12.1 d3@6.3.1 \
        @cernopendata/demobbed-viewer@v1.3.0 ispy-webgl@0.9.8-COD3.11 && \
    ln -s @cernopendata/demobbed-viewer /usr/lib/node_modules/ && \
    chgrp -R 0 "${INVENIO_INSTANCE_PATH}" && \
    chmod -R g=u "${INVENIO_INSTANCE_PATH}"

# Create `code` dir and set Invenio user as owner.
#
# The Debian base image creates the invenio user without a home directory
# (the AlmaLinux one did create /home/invenio), so anything that writes to
# $HOME -- git config --global, uv's cache -- fails. Create it here.
ENV CODE_DIR=/code
RUN mkdir ${CODE_DIR} && chown invenio:root ${CODE_DIR} && \
    mkdir -p /home/invenio && chown invenio:root /home/invenio && \
    chmod g=u /home/invenio

# Run application as Invenio user
USER ${INVENIO_USER_ID}

ENV UV_NO_CACHE=1

# --seed provides pip inside the virtualenv. run-tests.sh --check-pytest calls
# `pip install -e ".[tests]"`, and without a venv pip that resolves to
# /usr/local/bin/pip, which cannot write to /usr/local and silently falls back
# to a ~/.local user install that the virtualenv then ignores -- re-resolving
# the whole dependency tree for nothing.
RUN uv venv --seed "${WORKING_DIR}/src/.venv"

# The gfal2 bindings go straight into the virtualenv so that it does not need
# --system-site-packages.
COPY --from=gfal2-builder --chown=invenio:root /build/gfal2.so ${WORKING_DIR}/src/.venv/lib/python3.14/site-packages/gfal2.so

# Add CERN Open Data Portal sources to `code` and work there
WORKDIR ${CODE_DIR}
COPY . ${CODE_DIR}
USER root
RUN chown -R "${INVENIO_USER_ID}":root "${CODE_DIR}"
USER ${INVENIO_USER_ID}

# Debug off by default
ARG DEBUG=""
ENV DEBUG=${DEBUG:-""}

# Install CERN Open Data Portal sources.
#
# `insteadOf` is still required: the Flask-Markdown fork carries a git://
# submodule, a protocol GitHub disabled in 2022.
#
# setuptools is held below 81 because PyFilesystem2 (fs) still calls
# pkg_resources.declare_namespace() and invenio-accounts imports
# pkg_resources; setuptools 81+ no longer ships it.
#
# The install is editable even outside DEBUG. A non-editable install puts a
# copy under site-packages, create-instance.sh then imports it and leaves
# __pycache__ there; when --check-pytest later runs `pip install -e`, pip
# removes the .py files it recorded but not those .pyc files, and the orphaned
# tree -- having no __init__.py -- shadows the editable finder as a namespace
# package. Imports then resolve to __file__=None and coverage measures
# nothing. Installing editable once avoids the copy altogether, and makes
# coverage see /code/cernopendata, which is what Codecov expects.
# hadolint ignore=DL3013,SC2086
RUN git config --global url.https://github.com/.insteadOf git://github.com/ && \
    uv pip install "setuptools<81" && \
    uv pip install -e ".[all]" && \
    uv pip check

# Create instance
RUN scripts/create-instance.sh

# Configure uWSGI
ARG UWSGI_BUFFER_SIZE=8192
ENV UWSGI_BUFFER_SIZE ${UWSGI_BUFFER_SIZE:-8192}
ARG UWSGI_IDLE=60
ENV UWSGI_IDLE ${UWSGI_IDLE:-60}
ARG UWSGI_MAX_REQUESTS=1000
ENV UWSGI_MAX_REQUESTS ${UWSGI_MAX_REQUESTS:-1000}
ARG UWSGI_MAX_WORKER_LIFETIME=1800
ENV UWSGI_MAX_WORKER_LIFETIME ${UWSGI_MAX_WORKER_LIFETIME:-1800}
ARG UWSGI_PORT=5000
ENV UWSGI_PORT ${UWSGI_PORT:-5000}
ARG UWSGI_PROCESSES=4
ENV UWSGI_PROCESSES ${UWSGI_PROCESSES:-4}
ARG UWSGI_SOCKET_TIMEOUT=600
ENV UWSGI_SOCKET_TIMEOUT ${UWSGI_SOCKET_TIMEOUT:-600}
ARG UWSGI_THREADS=1
ENV UWSGI_THREADS ${UWSGI_THREADS:-1}
ARG UWSGI_WSGI_MODULE=cernopendata.wsgi:application
ENV UWSGI_WSGI_MODULE ${UWSGI_WSGI_MODULE:-cernopendata.wsgi:application}

# Start the CERN Open Data Portal application
# hadolint ignore=DL3025
CMD uwsgi \
        --buffer-size ${UWSGI_BUFFER_SIZE} \
        --cheap \
        --die-on-term \
        --enable-threads \
        --idle ${UWSGI_IDLE} \
        --master \
        --max-requests ${UWSGI_MAX_REQUESTS} \
        --max-worker-lifetime ${UWSGI_MAX_WORKER_LIFETIME} \
        --memory-report \
        --module ${UWSGI_WSGI_MODULE} \
        --need-app \
        --processes ${UWSGI_PROCESSES} \
        --py-call-osafterfork \
        --single-interpreter \
        --socket 0.0.0.0:${UWSGI_PORT} \
        --stats /tmp/stats.socket \
        --threads ${UWSGI_THREADS} \
        --vacuum \
        --wsgi-disable-file-wrapper \
        --socket-timeout ${UWSGI_SOCKET_TIMEOUT}
