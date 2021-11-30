import os
from workflow.extraction.utils.sql_utils import extract_coursera_sql_data
from workflow.extraction.utils.feature_utils import main as extract_features


def extract_data(course_name, num_weeks, label_type):
    dir = '/morf-data/' + course_name
    extract_coursera_sql_data(course_name)
    extract_features(course_name, label_type, num_weeks)
