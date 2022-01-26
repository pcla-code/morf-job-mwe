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

"""
Example of a minimum working example script for MORF 2.0.

Note that this script uses the --mode parameter from docker run to control the flow of extraction, training, and testing.

This script is structured to utilize the input and output contract of the extract_session() and train_course() functions from the MORF API.
"""

from workflow.extraction.extractors import extract_data
from workflow.extraction.utils.dataset_utils import build_course_dataset
from workflow.ml.train_test import train_test_course

if __name__ == "__main__":
    course_name = 'accounting_001'
    label_type = 'dropout'
    extract_data(course_name, 10, label_type)
    build_course_dataset(course_name, label_type)
    train_test_course(course_name)
