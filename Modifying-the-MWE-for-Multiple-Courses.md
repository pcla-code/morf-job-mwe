# Modifying the MWE for Multiple Courses

(By Alex Tobias)

Hello! This is a basic guide for helping users better understand how they might want to modify the MWE to suit their own purposes.

This guide focuses on a fairly simple change - getting the MWE to extract data from more than one course.

You may notice that currently, the MWE only extracts data from one course: "accounting". By following along with this guide, we will modify the MWE so that it draws from multiple courses.

The changes are actually really simple - only 3 files need to be modified:
- `mwe.py`
- `workflow/extraction/utils/dataset_utils.py`
- `workflow/ml/train_test.py`

The full modified version can be seen at [https://github.com/pcla-code/morf-job-mwe-multi-alex](https://github.com/pcla-code/morf-job-mwe-multi-alex).

A very useful resource are [these guides](https://github.com/alextobias/morf-mwe-alex-readme) that I've written regarding MORF and its MWE - especially [this one](https://github.com/alextobias/morf-mwe-alex-readme/blob/main/MWE-Walkthrough.md) which is a overview/walkthrough of the MWE. If you haven't seen it yet, I recommend you skim through it. Full links below:
- [https://github.com/alextobias/morf-mwe-alex-readme](https://github.com/alextobias/morf-mwe-alex-readme)
- [https://github.com/alextobias/morf-mwe-alex-readme/blob/main/MWE-Walkthrough.md](https://github.com/alextobias/morf-mwe-alex-readme/blob/main/MWE-Walkthrough.md)

We wil start by going over the changes to `mwe.py`, then `dataset_utils.py`, then `train_test.py`.

## Modifying `mwe.py`

Old:
```python
if __name__ == "__main__":
    course_name = 'accounting'
    label_type = 'dropout'
    extract_sessions(course_name)
    build_course_dataset(course_name, label_type)
    train_test_course(course_name)
```

New:
```python
if __name__ == "__main__":
    course_names = ['accounting', 'finance', 'worldmusic']
    label_type = 'dropout'

    # the ouput of extract_sessions is a csv in /temp-data/[course]/[session]/morf-mwe-feats.csv
    # so I think it's safe to loop over all course names in the extract_sessions step,
    # as the separate data does not need to be integrated yet
    for course_name in course_names:
        extract_sessions(course_name)

    # the output of build_course_dataset used to be a file /temp-data/[coursename]/course_dataset.csv
    # I've modified the output to be /temp-data/course_dataset.csv
    build_course_dataset(course_names, label_type)

    # train_test_course has minimal modification since it utilizes /course_dataset.csv from above
    # however, we've changed the path it gets saved to so we need to account for that in our changes to train_test_course
    # I've also changed it so that we pass the course_names list as a parameter, but to be honest, it goes unused in the function
    train_test_course(course_names)
```

The basic idea here is to replace our `course_name` strong with a list of strings which we will call `course_names`.

In the extraction phase, we can simply loop over each of our course names and call `extract_sessions` on it. This is fine to do because each time we call `extract_sessions`, it generates a CSV in the docker container called `/temp-data/[course]/[session]/morf-mwe-feats.csv`. 

All these CSVs will later be used by build_course_dataset, so it is ok to have a separate CSV generated per course per session. Then, we will need to modify `build_course_dataset` accordingly.

## Modifying `dataset_utils.py` (`build_course_dataset`)

Old:
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

New:
```python
def build_course_dataset(course_names, label_type):
    # move the initialization of features up here
    # as we loop through the courses, we'll add the data we read from the CSV into this features list
    features = []
    for course in course_names:
        dir = '/temp-data/' + course

        labels_train = pd.read_csv('/morf-data/labels-train.csv', low_memory=False)
        labels_train = labels_train[(labels_train['course'] == course) & (
            labels_train['label_type'] == label_type)]

        labels_test = pd.read_csv('/morf-data/labels-test.csv', low_memory=False)
        labels_test = labels_test[(labels_test['course'] == course) & (
            labels_test['label_type'] == label_type)]

        labels = pd.concat([labels_train, labels_test])
        # features used to be initialized here since before, we only cared about one course at a time
        for session in filter(os.path.isdir, [os.path.join(dir, curr_dir) for curr_dir in os.listdir(dir)]):
            features.append(pd.read_csv(session + '/morf_mwe_feats.csv'))

    # each time we append to features, the data header rows get appended as well
    # so that's why we do a concat here, to get rid of the extra header rows (I think, could be wrong)
    features = pd.concat(features)
    dataset = pd.merge(features, labels, on='userID')
    dataset.drop(columns=['userID', 'label_type',
                          'course', 'session'], inplace=True)
    # previously, we used to output the data to /temp-data/[coursename]/course_dataset.csv
    # now instead just save it to /temp-data/course_dataset.csv
    dataset.to_csv('/temp-data/course_dataset.csv', index=False)
    return
```

Again, what we do here is to accomodate the existence of multiple courses. So what we do now is to pass in `course_names` as a parameter, then loop through the courses, and concatenate our gathered data at the end.

What this outputs is a file `course_dataset.csv` Note that in the pre-multi-course version, the filepath is `/temp-data/[coursename]/course_dataset.csv`. Since we still only want one final csv being output, we just output to `/temp-data/course_dataset.csv`.

Since `train_test_course` utilizes this CSV file, we need to update it as well:


## Modifying `train_test.py` (`train_test_course`)

Old:
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

New:
```python
def train_test_course(course_names):
    # now, the course dataset is saved in /temp-data/course_dataset.csv so we reflect this change here
    dataset = pd.read_csv('/temp-data/course_dataset.csv')
    # the rest of this function is unchanged
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

You may be asking, "why not just loop over the course names and call `train_test_course` on each of them?"

The reason is that train_test_course generates `output.csv`, which is what MORF then uses to analyse the model. MORF will only look at one output.csv, so we should only call `train_test_course` once. Since `train_test_course` reads in `course_dataset.csv`, we needed the previous step to only generate one `course_dataset.csv` accounting for all the courses we wanted to look at.

That's why the only change we make here is to tell `train_test_course` to look at `/temp-data/course_dataset.csv` instead of `/temp-data/[course]/course_dataset.csv`.
