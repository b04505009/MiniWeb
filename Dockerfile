FROM ubuntu:16.04
MAINTAINER b04505009@ntu.edu.tw

RUN apt-get upgrade -y
RUN apt-get update

RUN apt-get install -y git sudo python python3 python3-pip default-jre
RUN git clone https://github.com/zander363/MiniWeb
WORKDIR /MiniWeb
RUN ./install.sh 
RUN pip3 install -r requirements.txt

CMD [ "python3", "-u", "server.py" ]
