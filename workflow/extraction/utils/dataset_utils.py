import os
import pandas as pd


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
