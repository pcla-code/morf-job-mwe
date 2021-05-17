FROM ubuntu:20.04

ENV TZ=US
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# install Python 
RUN apt update
RUN apt install -y python3-pip

# install Python libs
RUN pip3 install pandas numpy scikit-learn

# install MySQL and add configurations
RUN echo "mysql-server mysql-server/root_password password root" | debconf-set-selections && \
  echo "mysql-server mysql-server/root_password_again password root" | debconf-set-selections && \
  apt-get -y install mysql-server && \
  echo "secure-file-priv = \"\"" >>  /etc/mysql/mysql.conf.d/mysqld.cnf
RUN usermod -d /var/lib/mysql/ mysql

# add scripts
ADD mwe.py mwe.py
ADD workflow workflow

# define entrypoint
ENTRYPOINT ["python3", "mwe.py"]