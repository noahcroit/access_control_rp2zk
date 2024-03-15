# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

RUN apt update
RUN apt install -y python3 python3-pip

# Set working directory
WORKDIR /worker

# Set volume for configuration file
VOLUME ["/config"]
COPY worker/config.json /config/config.json

COPY worker .

# Copy requirements.txt and Install
RUN pip3 install -r requirements.txt

# Expose ports
EXPOSE 1883
EXPOSE 4370
EXPOSE 6379

# Run worker
CMD [ "python3", "worker_accessctrl.py", "--json", "/config/config.json"]
