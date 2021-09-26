import os
import pandas as pd


def build_course_dataset(course, label_type):
    dir = '/temp-data/' + course
    labels_train = pd.read_csv('/morf-data/labels-train-with-underscore.csv', low_memory=False)
    labels_train = labels_train[(labels_train['course'] == course) & (
        labels_train['label_type'] == label_type)]
    labels_test = pd.read_csv('/morf-data/labels-test-with-underscore.csv', low_memory=False)
    labels_test = labels_test[(labels_test['course'] == course) & (
        labels_test['label_type'] == label_type)]
    labels = pd.concat([labels_train, labels_test])
    features = pd.read_csv(dir + '/morf_mwe_feats.csv')
    dataset = pd.merge(features, labels, on='userID')
    dataset.drop(columns=['userID', 'label_type',
                          'course'], inplace=True)
    dataset.to_csv(dir + '/course_dataset.csv', index=False)
    return
