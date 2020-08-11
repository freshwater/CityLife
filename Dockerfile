
FROM ubuntu:latest

RUN apt-get update
RUN apt --yes upgrade

RUN apt-get install --yes python3
RUN apt-get install --yes python3-pip
RUN pip3 install --upgrade pip

RUN pip install psycopg2-binary

# RUN pip install python-dateutil 
# RUN python3 -c "from dateutil import tz"

COPY server.py .
COPY index.html .

VOLUME /database

ENTRYPOINT ["/bin/bash", "-c", "python3 -u server.py"]
