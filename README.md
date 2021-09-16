# MOOC Replication Framework (MORF)
The MORF Platform currently holds data from 2 institutions covering 209 unique sessions across 77 courses on the Coursera Spark platform, and 173 courses on the Coursera Phoenix Platform. The Spark data in MORF is in the Coursera platform data export format documented [here](https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf), while the Phoenix data is in a format documented here. Access to run analyses on this dataset is available for collaborative projects, and an institutional data use agreement is required in order to use the MORF Platform.

## So what do I need?
1. First you need to request an API key, you can do this via email
2. Next you will need to install two libraries
```python
pip install morf-job-api
pip install requests
```
## What should I submit?
We recommend you first run the [Minimum Working Example](MWEREADME.md).
If this sucessfully runs, you will know that your API key is valid and that you have the correct version of the API installed
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
