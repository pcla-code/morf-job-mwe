# MORF - Writing a Job
This document maintained by [Alex Tobias](https://github.com/alextobias) (for the [University of Pennsylvania Center for Learning Analytics]((https://www.upenn.edu/learninganalytics/)))

## Document Purpose (read this first)
Are you a researcher interested in applying machine learning to large educational data sets from massive open online courses (MOOCs)? If so, you are in the right place.

This document is to walk a user through the steps needed to submit a job to MORF. It goes over what a job is, what the components are, and what is neccessary to tell MORF to construct a model and run a job.

To do this, it walks the user through the simple minimum working example (MWE), which can be found here: [MORF MWE](https://github.com/pcla-code/morf-job-mwe)

Some of the notes here have been drawn from the [MORF documentation](https://educational-technology-collective.github.io/morf/documentation/), which is also a great resource.

## Overview
MORF is a platform where researchers can construct and evaluate predictive models from raw MOOC platform data. 

The MORF backend is a Flask application. It's normally hosted on an EC2 instance. Put simply, it accepts jobs, runs them according to the controller script, then emails the results to the submitter.

Jobs are submitted as HTTP requests to the MORF backend. Each 'job' contains a pointer to a Docker file, a controller script which is executed in the docker instance, and other metadata. The MWE is one such instance of a job.

If you would like to run an instance of the MORF backend yourself, [this document](Running_the_MORF_backend.md) contains what you need to know. 

The main steps to executing a job on MORF are (this is straight from the documentation):

- Write code to extract features from raw platform data and build predictive models on the results of that feature extraction.
- Write a high-level “controller script” using the MORF Python API.
- Build a Docker image containing your code and any software dependencies with the appropriate control flow.
- Create a configuration file containing identifiers and links to your controller script and docker image.
- Upload the the controller script, docker image, and configuration file to public locations (you need to provide either HTTPS or S3 URLs to these files).
- Submit your job to the MORF web API. You will receive notifications and results via email as your job is queued, initiated, and completed.

This document will walk you through each of these steps in the context of the MORF MWE (minimum working example).

## Platform Data

When a job is submitted to MORF, it is able to extract data that the MORF backend has access too.

MORF's data currently consists of several datasets from Coursera. The data policy can be found [here](https://docs.google.com/document/d/1oZNkaPDRG0wgJTcIS7viqE-KhENr4skhOQ3vc9s_xSw/edit#heading=h.gjdgxs).

A very thorough explanation from Coursera on the way data is exported and structured can be found here: [https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf](https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf) (If the link is broken, search for "Coursera Data Export Procedures")

The following is another excellent resource on the database schema: [https://wiki.illinois.edu/wiki/display/coursera/Coursera+Session-Based+Courses+SQL+and+Eventing+Data+Tables+Documentation](https://wiki.illinois.edu/wiki/display/coursera/Coursera+Session-Based+Courses+SQL+and+Eventing+Data+Tables+Documentation)

Here are some key things that you should know about the way data is stored and accessed in MORF:

### Directory Structure and files
The following is an example of how a course data directory is structured in our backend, which is identical to how it's given in Coursera's "Data Exports" document above.

- `accounting` (course name)
    - `001` (session)
        - `accounting-001_clickstream_export.gz` (holds the clickstream data in JSON format)
        - `An Introduction to Financial Accounting (accounting-001)_Demographics_individual_responses.csv` 
            - This holds self-reported demographic information about users such as location, gender, etc.
        - `An Introduction to Financial Accounting (accounting-001)_Demographics_summary.html` 
            - This is a browser-viewable HTML visualization of demographic survey responses - you will likely not need to use this.
        - `An Introduction to Financial Accounting (accounting-001)_SQL_anonymized_forum.sql.gz`
            - Contains all data related to the course forum's threads, posts and comments. 
        - `An Introduction to Financial Accounting (accounting-001)_SQL_anonymized_general.sql.gz` (almost everything else in the course - see notes in following section)
            - This database will contain almost everything else in the course, for example: access groups, announcements, grades, lecture metadata, quiz metadata, and users
        - `An Introduction to Financial Accounting (accounting-001)_SQL_hash_mapping.sql.gz` 
            - A single table linking anonymized user ids across tables in the other datasets)
        - `An Introduction to Financial Accounting (accounting-001)_SQL_unanonymizable.sql.gz` 
            - contains misc. unanonymizable data, not very useful)

The clickstream data is stored in JSON format. 

The other files (with the exception of the HTML file) are flat SQL files, so they  contain not only the data itself, but also the SQL commands needed to set up the tables, import the data, etc. Running them in MySQL will automatically set everything up for you. 

**Because the data is stored in these flat JSON/SQL files, this is how you'll need your job to interact with the course data:**
- Use the dockerfile to specify that MySQL should be installed in the docker container that will be created for running your job.
- In your job script, import the SQL files into the MySQL instance that runs inside your docker container.
- In your job script, run SQL queries to obtain the data needed for your feature extraction.

This is important to understand since the MORF backend itself doesn't run a MySQL instance - each job must instantiate its own MySQL instance in its docker container.


## Docker & MORF

This section describes some Docker basics for using the MORF platform, including creating Dockerfiles and building images from Dockerfiles. It also gives some additional information on how MORF runs Docker images internally and what command line arguments any submitted Docker image needs to accept.

This document assumes you have Docker installed. For more information about Docker, including installation instructions, see [Docker installation instructions](https://docs.docker.com/engine/install/) and [Getting Started with Docker](https://docs.docker.com/get-started/).

The Docker image you provide will be run in a non-networked environment with /input/ and /output/ directories mounted in its filesystem.

### Creating a project Dockerfile

A Dockerfile is a text file that contains instructions for building your Docker image. The exact contents of this file depend on (a) the software dependencies of your MORF project code, which may include (for example) scripts written in Python, Java, R, or other languages; and (b) the actual code needed to run for your MORF workflow (feature extraction, training, and testing). You can create this file using any text editor; save it with no extension and name it dockerfile. 

**note - outdated, to remove**
Note that, because the Docker image does not have network access (for security reasons), any required libraries or software packages required by your code should be installed in the Docker image.

Let's look at what the MWE dockerfile looks like:

### Dockerfile
```Dockerfile
# Specifies that our base image will be ubuntu 20.04
FROM ubuntu:20.04

# install Python 
RUN apt update
RUN apt install -y python3-pip

# install Python libraries
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
```

Visit the [dockerfile documentation](https://docs.docker.com/engine/reference/builder/) for more detail on what these instructions tell docker to do. 

This Dockerfile has seven distinct steps, and demonstrates a typical workflow for MORF which uses Python3 and mySQL. Let’s walk through each step.

#### 1) Pull base image
```dockerfile
FROM ubuntu:20.04
```
This command defines the base ubuntu 20.04 image to use as the first layer for building the Docker image.

We recommend starting from one of Docker’s base images unless the environment you need isn’t available. Check the official [Docker library](https://github.com/docker-library/official-images/tree/master/library) for a list of available image tags.

#### 2) Install Python (python3) and libraries (pandas, numpy, scikit-learn)
```dockerfile
# install Python 
RUN apt update
RUN apt install -y python3-pip

# install Python libraries
RUN pip3 install pandas numpy scikit-learn
```
These commands use the Docker keyword RUN to define commands that should be literally executed in the image. Note that each of these commands would normally by entered at an ubuntu command line prompt; Docker does this when building the image.

We also use pip to install Python libraries that are used in the feature extraction and modeling code in the MWE.

#### 3) Install configure, and run MySQL
```dockerfile
RUN echo "mysql-server-5.7 mysql-server/root_password password root" | sudo debconf-set-selections && \
  echo "mysql-server-5.7 mysql-server/root_password_again password root" | sudo debconf-set-selections && \
  apt-get -y install mysql-server-5.7 && \
  echo "secure-file-priv = \"\"" >>  /etc/mysql/mysql.conf.d/mysqld.cnf
RUN usermod -d /var/lib/mysql/ mysql
```
This step installs mySQL, sets the root password, and sets the secure-file-priv option to allow for exporting of query results to a file (using mySQL’s INTO OUTFILE command requires setting this option).

The database exports in MORF are provided as MySQL dumps, and accessing them requires mySQL. Jobs that do not use data from the MySQL dumps can skip this step.

The last line starts MySQL. An alternative is simply `RUN service mysql start`.

#### 4) Add scripts
```dockerfile
# add scripts
ADD mwe.py mwe.py
ADD workflow workflow
```
This step adds scripts and directories from the local directory to the dockerfile itself.

What we are doing here is adding scripts from the 'workflow' folder, which are used in the extract, train, and test workflow; mwe.py is a simple script that reads the input from the docker run command in MORF and uses it to control the flow of execution.

Any modules, code, or other files you want to be available inside your Docker image during execution must be added by using ADD in your dockerfile; no code can be downloaded or installed during execution.

#### 5) Define entrypoint
```dockerfile
ENTRYPOINT ["python3", "mwe.py"]
```
This command uses Docker’s ENTRYPOINT keyword to define an entrypoint for execution.

Whenever this image is executed by MORF, this line tells the image to automatically execute python3 mwe.py instead of entering any other shell. Note that MORF will also pass the --mode flag used to control the script when calling your script, so whichever script is defined as the ENTRYPOINT should expect a command-line argument for mode which takes the values described below.





