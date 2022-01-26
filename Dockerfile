FROM ubuntu:20.04

# install Python 
RUN apt update
RUN apt install -y python3-pip
RUN apt update
RUN apt install -y iputils-ping
RUN apt install -y net-tools
RUN apt install -y curl
RUN apt install -y wget
RUN pip install requests
RUN pip install pandas
RUN pip install numpy
RUN pip install scikit-learn
RUN apt install -y nano
# add scripts
ADD mwe.py mwe.py
ADD workflow workflow
# define entrypoint
ENTRYPOINT ["python3", "mwe.py"]