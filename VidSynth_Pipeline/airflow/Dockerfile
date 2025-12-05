# Use the official Apache Airflow image
FROM apache/airflow:2.8.1

# Install the 'requests' library so our DAG can make HTTP calls
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir requests
