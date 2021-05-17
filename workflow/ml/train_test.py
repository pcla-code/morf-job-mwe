import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


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
