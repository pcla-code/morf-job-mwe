# MORF-MWE-WALKTHROUGH

This file walks you through the different pieces of the MWE and what they do.
It was written by [Alex Tobias](https://github.com/alextobias) (for the [University of Pennsylvania Center for Learning Analytics]((https://www.upenn.edu/learninganalytics/))) and edited by [Stephen Hutt](https://github.com/stephenhutt)

Table of Contents
=================

* [MORF-MWE-WALKTHROUGH](#morf-mwe-walkthrough)
   * [Dockerfile](#dockerfile)
   * [Minimum Working Example - <strong>mwe.py</strong>](#minimum-working-example---mwepy)
      * [Extracting the Data - <strong>extract_sessions</strong>](#extracting-the-data---extract_sessions)
         * [Extracting Data from Coursera <strong>extract_coursera_sql_data</strong>](#extracting-data-from-coursera-extract_coursera_sql_data)
         * [Pulling Features <strong>extract_features</strong>](#pulling-features-extract_features)
         * [<strong>extract_users</strong>](#extract_users)
      * [<strong>build_course_dataset</strong>](#build_course_dataset)
      * [<strong>train_test_course</strong>](#train_test_course)
   * [After job execution](#after-job-execution)


## Dockerfile
```Dockerfile
# Specifies that our base image will be ubuntu 20.04
FROM ubuntu:20.04

# install Python
RUN apt update
RUN apt install -y python3-pip

# install Python libraries
RUN pip3 install pandas numpy scikit-learn

# install MySQL and add configurations
# The database exports in MORF are provided as MySQL dumps, and accessing them requires MySQL.
# Jobs that do not use data from the MySQL dumps can skip this step.
RUN echo "mysql-server mysql-server/root_password password root" | debconf-set-selections && \
  echo "mysql-server mysql-server/root_password_again password root" | debconf-set-selections && \
  apt-get -y install mysql-server && \
  echo "secure-file-priv = \"\"" >>  /etc/mysql/mysql.conf.d/mysqld.cnf
RUN usermod -d /var/lib/mysql/ mysql

# add scripts and directories from the local directory to the dockerfile itself
ADD mwe.py mwe.py
ADD workflow workflow

# define entrypoint
ENTRYPOINT ["python3", "mwe.py"]
```

Visit the [dockerfile documentation](https://docs.docker.com/engine/reference/builder/) for more detail on what these instructions tell docker to do.

The line `ENTRYPOINT ["python3", "mwe.py"]` specifies that the dockerpoint will use `mwe.py` as an entrypoint for execution. Let's look at `mwe.py` now.


## Minimum Working Example - **`mwe.py`**

```python
from workflow.extraction.extractors import extract_sessions
from workflow.extraction.utils.dataset_utils import build_course_dataset
from workflow.ml.train_test import train_test_course

if __name__ == "__main__":
    # MODIFY according to your needs
    course_name = 'accounting'
    label_type = 'dropout'
    extract_sessions(course_name)
    build_course_dataset(course_name, label_type)
    train_test_course(course_name)
```

The first thing we do is import our main job functions from the `workflow` folder. We also specify the course name and label type used in this job, which you will likely need to change to suit your purposes.

You can see that the MWE structures its job in 3 main steps:

1) `extract_sessions`
- This is where course session data is pulled and features are extracted.
- The result of this is a variety of CSVs containing results queried from the course data.
- These CSVs are stored in the docker container, and are separated by course and session in a folder `/temp-data/` (e.g. `/temp-data/accounting/001`)

2) `build_course_dataset`
- This step combines the data obtained from each course & session, and performs feature extraction on the data.
- The result of this is a file `course_dataset.csv`, again local to the docker container.
- This csv file will be used in the next step to construct a model.

3) `train_test_course`
- This step takes `course_dataset.csv` and performs a logistic regression on it, and then assesses the accuracy of the model.
- The output of this step is a file `output.csv.`, which is not local to the docker container, but is saved in the MORF backend.

**After** the steps in the job are executed, the MORF backend takes `output.csv`, and evaluates it on a variety of metrics, such as its accuracy, Cohen's kappa, etc. This produces a file, eval.csv, which gets emailed to the address specified in the job submission. **This step is done by the MORF backend for every job, so you won't see code for this in the MWE example.**

Let's look now at `extract_sessions`:

### Extracting the Data - **`extract_sessions`**
```python
def extract_sessions(course_name):
    dir = '/morf-data/' + course_name
    for session in filter(os.path.isdir, [os.path.join(dir, curr_dir) for curr_dir in os.listdir(dir)]):
        extract_coursera_sql_data(course_name, session.split('/')[-1])
        extract_features(course_name, session.split('/')[-1])
```

Here, the MWE takes the supplied course name ("accounting", in this case), and loops through each session offered under the course name.

We now have two functions, `extract_coursera_sql_data` and `extract_features`, which are executed for each course session.

Let's now take a look at extract_coursera_sql_data:

#### Extracting Data from Coursera **`extract_coursera_sql_data`**
```python
def extract_coursera_sql_data(course, session, forum_comment_filename="forum_comments.csv", forum_post_filename="forum_posts.csv"):
    """
    Initialize the mySQL database, load files, and execute queries to deposit csv files of data into /input/course/session directory.
    :param course: course name.
    :param session: session id.
    :param forum_comment_filename: name of csv file to write forum comments data to.
    :param forum_post_filename: name of csv file to write forum posts to.
    :return:
    """

    # NOTE: some lines ommitted from this tutorial, to reduce clutter. # It is expected that you will have the actual MWE to reference from.
    course_session_dir = os.path.join("/morf-data/", course, session)

    # obtains the paths to the hash_mapping and anonymized_forum files for this session
    # MODIFY according to your needs
    hash_mapping_sql_dump = \
        [x for x in os.listdir(course_session_dir)
         if "hash_mapping" in x and session in x][0]
    forum_sql_dump = \
        [x for x in os.listdir(course_session_dir)
         if "anonymized_forum" in x and session in x][0]

    # this function starts a running mysql process in the docker container
    initialize_database()

    # takes the paths to the SQL files specified above and loads them into the SQL process
    # MODIFY according to your needs
    load_mysql_dump(os.path.join(course_session_dir, forum_sql_dump))
    load_mysql_dump(os.path.join(course_session_dir, hash_mapping_sql_dump))

    # MODIFY according to your needs
    # Note that the resulting csv filenames are forum_comment_filename and forum_post_filename, which are specified as default parameters to this function.
    # You should also mofidy these appropriately if applicable.
    # execute forum comment query and send to csv
    query = """SELECT thread_id , post_time , b.session_user_id FROM forum_comments as a LEFT JOIN hash_mapping as b ON a.user_id = b.user_id WHERE a.is_spam != 1 ORDER BY post_time;"""
    subprocess.call("mkdir -p " + "/temp-data/" + course + '/' +
                    course_session_dir.split("/")[-1], shell=True)
    execute_mysql_query_into_csv(query, os.path.join(
        "/temp-data/" + course + '/' + course_session_dir.split("/")[-1], forum_comment_filename))
    # execute forum post query and send to csv
    query = """SELECT id , thread_id , post_time , a.user_id , public_user_id , session_user_id , eventing_user_id FROM forum_posts as a LEFT JOIN hash_mapping as b ON a.user_id = b.user_id WHERE is_spam != 1 ORDER BY post_time;"""
    execute_mysql_query_into_csv(query, os.path.join(
        "/temp-data/" + course + '/' + course_session_dir.split("/")[-1], forum_post_filename))
    return
```

The important takeaways from here are that:
- **This step starts the SQL database, loads our specified SQL dumps, and runs queries on our tables, which are saved to CSVs in a `/temp-data/` folder.**
- A mysql process local to the docker container is initialized using `initialize_database`.
- The `load_mysql_dump` function takes the path to a sql file, and loads it into the database. Here, the MWE specifies that the "hash_mapping" and "anonymized_forum" SQL files in each session folder should be loaded into the database, but you will likely need to modify this.
- You will also need to modify the queries into the DB to extract whatever data you need.
- Notice that the MWE creates a `/temp-data/` folder, which is a **folder local to the Docker container** where the output from the queries will go.
- The `execute_mysql_query_into_csv` function calls execute the specified queries and save them to CSVs in the aforementioned `/temp-data/` folder.
- To understand the database schema in more depth, you can refer to these links:
  - [https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf](https://spark-public.s3.amazonaws.com/mooc/data_exports.pdf)


Now that our queries have been executed and saved as CSV files, let's look at the `extract_features` function.

#### Pulling Features **`extract_features`**
```python
def main(course, session, n_feature_weeks=4, out_dir="/temp-data"):
    """
    Extract counts of forum posts by week and write to /output.
    :param course: Coursera course slug (string).
    :param session: 3-digit run number (string).
    :param n_feature_weeks: number of weeks of features to consider (int).
    :return: None; writes output for weekly CSV file in /output.
    """
    session_dir = "/morf-data/{0}/{1}/".format(course, session)
    temp_dir = "/temp-data/{0}/{1}/".format(course, session)
    clickstream = [x for x in listdir(
        session_dir) if x.endswith("clickstream_export.gz")][0]
    clickstream_fp = "{0}{1}".format(session_dir, clickstream)
    forumfile = "{0}forum_posts.csv".format(temp_dir)
    commentfile = "{0}forum_comments.csv".format(temp_dir)
    datefile = "{0}coursera_course_dates.csv".format('/morf-data/')
    course_start, course_end = fetch_start_end_date(course, session, datefile)
    # build features
    print("Extracting users...")
    users = extract_users(clickstream_fp, course_start, course_end)
    print("Complete. Extracting features...")
    feats_df = extract_features(
        forumfile, commentfile, users, course_start, course_end)
    # write output
    generate_weekly_csv(feats_df, out_dir=out_dir + '/' +
                        course + '/' + session, i=n_feature_weeks)
    print("Output written to {0}".format(out_dir))
```

This step obtains the `forum_posts.csv` and `forum_comments.csv` files we output as a result of the `extract_coursera_sql_data` step.

It then performs feature extraction on this data, which you will want to modify according to your own needs.

The result of this feature extraction is a table where rows are users, columns are weeks, and data points are how many forum posts that user made that particular week for that course session, output as `/[course]/[session]/morf_mwe_feats.csv`.

The result of this feature extraction is a table of userID, week number, and the number of forum posts that that user made that week.

e.g.
| userID | week | forum_posts |
| ------ | ---- | ----------- |
| a2f2ed432d514461136c895ab8bc47e23fd0011d | 0 | 0 |
| a2f2ed432d514461136c895ab8bc47e23fd0011d | 1 | 0 |
| a2f2ed432d514461136c895ab8bc47e23fd0011d | 2 | 0 |
| ...                                      | ... | ... |
| dba1c435cdfdaa383458560cf2969c404895abe8 | 10 | 0 |



**Recall that `extract_sessions` calls `extract_coursera_sql_data` and `extract_features` in a loop, for every session of the course. So each CSV output that we get here is still on a per-session basis. That's where the next part comes in; we need to combine this data across all sessions.**

If you are interested in how the feature extraction is done here, you may look through the code for the MWE. It is mostly CSV manipulation and data wrangling.

However, I will point out the `extract_users` function used here, which is where we extract user IDs from the clickstream file. The reason why the clickstream file wasn't used in the `extract_coursera_sql_data` step is because the clickstream is in JSON format, not SQL. So, you may find the following example code useful to extract data from the clickstream file.

#### **`extract_users`**
```python
def extract_users(coursera_clickstream_file, course_start, course_end):
    """
    Assemble list of all users in clickstream.
    :param coursera_clickstream_file: gzipped Coursera clickstream file
    :param course_start: datetime object for first day of course (generated from user input)
    :param course_end: datetime object for last day of course (generated from user input)
    :return: Python set of all unique user IDs that registered any activity in clickstream log
    """
    users = set()
    linecount = 0  # indexes line number
    with gzip.open(coursera_clickstream_file, "r") as f:
        for line in f:
            try:
                log_entry = loads(line.decode("utf-8"))
                user = log_entry.get("username")
                users.add(user)
            except ValueError as e1:
                print("Warning: invalid log line {0}: {1}".format(
                    linecount, e1))
            except Exception as e:
                print("Warning: invalid log line {0}: {1}\n{2}".format(
                    linecount, e, line))
            linecount += 1
    return users
```

### **`build_course_dataset`**
Now we move onto the second major step, `build_course_dataset`, which combines all these per-session tables into one table for the whole course.

```python
def build_course_dataset(course, label_type):
    dir = '/temp-data/' + course
    labels_train = pd.read_csv('/morf-data/labels-train.csv', low_memory=False)
    labels_train = labels_train[(labels_train['course'] == course) & (
        labels_train['label_type'] == label_type)]
    labels_test = pd.read_csv('/morf-data/labels-test.csv', low_memory=False)
    labels_test = labels_test[(labels_test['course'] == course) & (
        labels_test['label_type'] == label_type)]
    labels = pd.concat([labels_train, labels_test])
    features = []
    for session in filter(os.path.isdir, [os.path.join(dir, curr_dir) for curr_dir in os.listdir(dir)]):
        features.append(pd.read_csv(session + '/morf_mwe_feats.csv'))
    features = pd.concat(features)
    dataset = pd.merge(features, labels, on='userID')
    dataset.drop(columns=['userID', 'label_type',
                          'course', 'session'], inplace=True)
    dataset.to_csv(dir + '/course_dataset.csv', index=False)
    return
```

What this code is doing is taking all the CSVs we previously generated, (each user's forum posts each week during each course session), and combining them into one table. It also adds a column to indicate whether that student dropped the course or not. (The `label_type` variable was passed in as 'dropout').

You may look through the code if you wish to understand what it's doing in greater depth, but it is mostly data wrangling.

The resulting table looks like this:

|   | userID | week_0_forum_posts | week_1_forum_posts | ... | week_4_forum_posts | label_type | label_value | course | session |
|---|--------|--------------------|--------------------|-----|--------------------|------------|-------------|--------|---------|
| 0 | a2f2ed432d514461136c895ab8bc47e23fd0011d | 0 | 0 | ... | 0 | dropout | 1 | accounting | 001 |
| 1 | a2f2ed432d514461136c895ab8bc47e23fd0011d | 0 | 0 | ... | 0 | dropout | 1 | accounting | 001 |
| .... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| 113905 | dba1c435cdfdaa383458560cf2969c404895abe8 | 0 | 0 | ... | 0 | dropout | 1 | accounting | 001 |

This is output to `/temp-data/course_dataset.csv`, which is again only local to the docker container.


Now we move on to the final major part of the job, `train_test_course`.

### **`train_test_course`**

```python
def train_test_course(course):
    dataset = pd.read_csv('/temp-data/' + course + '/course_dataset.csv')
    X = dataset.drop(['label_value'], axis=1)
    y = dataset['label_value']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, stratify=y, random_state=1)
    clf = LogisticRegression(random_state=1)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_score = clf.predict_proba(X_test)
    output = pd.DataFrame({'y_true': y_test, 'y_pred': y_pred, 'y_score': [
                          proba[1] for proba in y_score]})
    output.to_csv('/output/output.csv', index=False)
```

Now, we take the `course_dataset.csv` file we generated in the last step, and open it as a pandas DataFrame.

We use `train_test_split` to split our data into random train and test subsets. Then we fit a logistic regression to the training subset.

Note where we use `random_state=1`. By providing an integer to seed random number generation, we can produce the same results across different calls. Please consider reproducibility when writing MORF jobs. For more information, see the [sklearn documentation](https://scikit-learn.org/stable/glossary.html#term-random_state) on `random_state`.

Next, we predict class labels, and obtain probability estimates for samples in our test data. This is then written to `/output/output.csv`, which looks like this:

| y_true | y_pred | y_score |
| ------ | ------ | ------- |
|  1  |  1  | 0.743688119086647 |
|  1  |  1  | 0.743688119086647 |
|  1  |  1  | 0.743688119086647 |
| ... | ... | ... |


**This `output.csv` is **NOT** local to the dockerfile; it is saved to MORF for evaluation**. For data privacy reasons, users do not have direct access to the `output.csv` file.


## After job execution

This concludes the execution of the MWE. The result, `output.csv` is then evaluated by MORF on a variety of statistical scores, resulting in a file `eval.csv`, which will be emailed to the submitter when the evaluation has finished.
