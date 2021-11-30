import os
from workflow.extraction.utils.sql_utils import extract_coursera_sql_data
from workflow.extraction.utils.feature_utils import main as extract_features


def extract_sessions(course_name, label_type):
    dir = '/morf-data/' + course_name
    for session in filter(os.path.isdir, [os.path.join(dir, curr_dir) for curr_dir in os.listdir(dir)]):
        extract_coursera_sql_data(course_name, session.split('/')[-1])
        extract_features(course_name, session.split('/')[-1], label_type)
