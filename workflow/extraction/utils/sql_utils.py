# Copyright (c) 2018 The Regents of the University of Michigan
# and the University of Pennsylvania
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import subprocess
import logging

DATABASE_NAME = "course"
TEMP_DIR = "/temp-data/"


def execute_mysql_query_into_csv(query, file, database_name=DATABASE_NAME):
    """
    Execute a mysql query into a file.
    :param query: valid mySQL query as string.
    :param file: csv filename to write to.
    :return: none
    """
    logging.info("executing sql query {} into csv file {}".format(query, file))
    mysql_to_csv_cmd = """ | tr '\t' ',' """  # string to properly format result of mysql query
    command = '''mysql -u root -proot {} -e"{}"'''.format(database_name, query)
    command += """{} > {}""".format(mysql_to_csv_cmd, file)
    subprocess.call(command, shell=True)
    return


def load_mysql_dump(dumpfile, database_name=DATABASE_NAME):
    """
    Load a mySQL data dump into DATABASE_NAME.
    :param file: path to mysql database dump
    :return:
    """
    logging.info("loading dump from {}".format(dumpfile))
    command = '''zcat {} | mysql -u root -proot {}'''.format(
        "\"" + dumpfile + "\"", database_name)
    subprocess.call(command, shell=True)
    return


def initialize_database(database_name=DATABASE_NAME):
    """
    Start mySQL service and initialize mySQL database with database_name.
    :param database_name: name of database.
    :return:
    """
    logging.info("initializing db ...")
    # start mysql server
    subprocess.call("service mysql start --log-error-verbosity=1", shell=True)
    # drop database if it exists
    subprocess.call(
        '''mysql -u root -proot -e "DROP DATABASE IF EXISTS {}"'''.format(database_name), shell=True)
    # create database
    subprocess.call(
        '''mysql -u root -proot -e "CREATE DATABASE {}"'''.format(database_name), shell=True)
    return


def extract_coursera_sql_data(course, session, forum_comment_filename="forum_comments.csv", forum_post_filename="forum_posts.csv"):
    """
    Initialize the mySQL database, load files, and execute queries to deposit csv files of data into /input/course/session directory.
    :param course: course name.
    :param session: session id.
    :param forum_comment_filename: name of csv file to write forum comments data to.
    :param forum_post_filename: name of csv file to write forum posts to.
    :return:
    """
    logging.basicConfig(filename='/output/logs.log', level=logging.DEBUG)
    course_session_dir = os.path.join("/morf-data/", course, session)
    hash_mapping_sql_dump = \
        [x for x in os.listdir(course_session_dir)
         if "hash_mapping" in x and session in x][0]
    forum_sql_dump = \
        [x for x in os.listdir(course_session_dir)
         if "anonymized_forum" in x and session in x][0]
    initialize_database()
    load_mysql_dump(os.path.join(course_session_dir, forum_sql_dump))
    load_mysql_dump(os.path.join(course_session_dir, hash_mapping_sql_dump))
    # execute forum comment query and send to csv
    query = """SELECT thread_id , post_time , b.session_user_id FROM forum_comments as a LEFT JOIN hash_mapping as b ON a.user_id = b.user_id WHERE a.is_spam != 1 ORDER BY post_time;"""
    subprocess.call("mkdir -p " + "/temp-data/" + course + '/' +
                    course_session_dir.split("/")[-1], shell=True)
    logging.debug(os.path.join("/temp-data/" + course + '/' +
                               course_session_dir.split("/")[-1], forum_comment_filename))
    execute_mysql_query_into_csv(query, os.path.join(
        "/temp-data/" + course + '/' + course_session_dir.split("/")[-1], forum_comment_filename))
    # execute forum post query and send to csv
    query = """SELECT id , thread_id , post_time , a.user_id , public_user_id , session_user_id , eventing_user_id FROM forum_posts as a LEFT JOIN hash_mapping as b ON a.user_id = b.user_id WHERE is_spam != 1 ORDER BY post_time;"""
    logging.debug(os.path.join("/temp-data/" + course + '/' +
                               course_session_dir.split("/")[-1], forum_post_filename))
    execute_mysql_query_into_csv(query, os.path.join(
        "/temp-data/" + course + '/' + course_session_dir.split("/")[-1], forum_post_filename))
    return
