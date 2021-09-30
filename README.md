# MOOC Replication Framework (MORF)
The MORF Platform currently holds data from 2 institutions covering 209 unique sessions across 77 courses on the Coursera Spark platform, and 173 courses on the Coursera Phoenix Platform. The Spark data in MORF is in the Coursera platform data export format documented [here](https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf), while the Phoenix data is in a format documented here. Access to run analyses on this dataset is available for collaborative projects, and an institutional data use agreement is required in order to use the MORF Platform.

MORF allows researchers to perform computation on a growing dataset without ever
having direct access to the data, so as to protect student privacy. Right now
these analyses are predominantly predictive modelling tasks, for example
investigating which feature sets are most predictive of student dropout.

MORF is constantly under development and if there is something that you would
like to do with MORF that it not currently possible, we would love to hear from
you!

## So what is a MORF Job?
A MORF job has two major components (1) Code to submit your job and (2) Code to
build and run your job. Both components are outline below.

### Code to submit
This will be a short python script (an example is at the end of this page)
that loads your API key and
your code and passes it to MORF. Once you run this code, your job will be in the
queue and you can wait for your results to be delivered via email.

### Code to Build and Run
Here we can again split into two parts. Building your MORF environment is relative to
whatever you want to do. Through a short docker file, you specific which pogramming
languages and packages need to be installed for your analysis. MORF will build a
container to your specifications to make sure that your code runs. An example
docker file can be seen in the [Minimum Working Example](MWEREADME.md).
If your analysis is in python, it is likely you can use a docker file very similar to this example.

When it comes to the code for your analysis, you have more freedom. You can control
what data is pulled from the MORF database and how it is then processed. Your predictive models
can be as complex, or as simple as you like. To aid you in extracting your
features, we have some sample data avaialble upon request.

## So what do I need?
1. First you need to request an API key, you can do this via email
2. Next you will need to install two libraries
```python
pip install morf-job-api
pip install requests
```
## What should I submit?
We recommend you first submit the [Minimum Working Example](MWEREADME.md).
If this sucessfully runs, you will know that your API key is valid and that you have the correct version of the API installed.
In the documentation we point out where each step of the processes is happening. You can also experiment with minor alterations.
## How do I submit?
Once you have your job ready you'll need to write a short script to submit it. An example is below.
```python
import morfjobapi as morf
BACKEND_URL = 'https://morf-pcla.education/api/jobs'
JOB_ZIP_FILE_LOCATION = 'path_to_morf-job-mwe-main.zip'
API_KEY = 'your_API_key'
job_config = {
 'job_zip_file': JOB_ZIP_FILE_LOCATION,
 'morf_api_endpoint': BACKEND_URL,
 'api_key': API_KEY
}
```

## What's Next?
Next you can start [creating your own job](Creatint_A_Job.md)
