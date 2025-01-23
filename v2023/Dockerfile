# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

RUN apt-get update -y && apt-get install -y \
			git \
			build-essential \
			iputils-ping \
			iproute2
			
RUN apt-get install -y python3 python3-pip

# build & install pyzk manually
RUN mkdir /build
RUN cd /build && git clone https://github.com/fananimi/pyzk.git
RUN cd /build/pyzk && python3 setup.py install

# Copy worker into container
RUN mkdir /worker
COPY ./worker /worker
 
# Set volume for configuration file
RUN cd /worker && mkdir /data
VOLUME ["/worker/data"]

# Copy requirements.txt and Install
RUN cd /worker && pip3 install -r requirements.txt

# Expose ports
#EXPOSE 1883
#EXPOSE 4370
#EXPOSE 6379

# Run worker
WORKDIR /worker
CMD [ "python3", "worker_accessctrl.py", "--json", "config2.json"]
