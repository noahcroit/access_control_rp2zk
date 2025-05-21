FROM python:3.10

COPY acworker.py door.py config.json requirements.txt /home/acworker/

WORKDIR /home/acworker/

RUN apt-get update && apt-get upgrade -y
RUN python -m pip install -r requirements.txt
RUN apt-get install -y tzdata

ENV TZ=Asia/Bangkok

EXPOSE 8080
EXPOSE 80
EXPOSE 1883
EXPOSE 6379

CMD ["python", "acworker.py", "-c", "config.json"]
