FROM continuumio/miniconda3:4.5.4
MAINTAINER Alex Waldrop "awaldrop@rti.org"

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app

RUN apt-get clean && rm -rf /var/lib/apt/lists/* && apt-get clean
RUN apt-get update -y && apt-get install -y --fix-missing -f build-essential libfreetype6-dev libpng-dev pkg-config libopenblas-dev cython

RUN conda create -n drug-name-coder-api python=3.6
RUN echo "source activate drug-name-coder-api" > ~/.bashrc
ENV PATH /opt/conda/envs/drug-name-coder-api/bin:$PATH

RUN pip install -r requirements.txt

COPY . /app
EXPOSE 8080
ENTRYPOINT ["/opt/conda/envs/drug-name-coder-api/bin/gunicorn", "app:app", "-b", "0.0.0.0:8080"]
