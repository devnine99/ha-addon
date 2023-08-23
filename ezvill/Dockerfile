FROM python:3.9-slim-buster

ENV LANG C.UTF-8
ENV TZ=Asia/Seoul

RUN python3 -m pip install paho-mqtt

COPY run.sh /
COPY main.py /

WORKDIR /share

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
