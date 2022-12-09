#!/usr/bin/env python
#
# Loop across Google Forms, fetch responses, analyze them and output average grade in a CSV file.
# Useful for the courses GBM6125 and GBM6904 at Polytechnique Montreal.
#
# Useful documentation
# - https://developers.google.com/drive/api/guides/search-files
# - https://developers.google.com/forms/api/guides/retrieve-forms-responses?hl=en
# - https://pythonhosted.org/PyDrive/quickstart.html#authentication
#
# Author: Julien Cohen-Adad

# import requests
import coloredlogs
import logging
import numpy as np
import pandas as pd
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools


# Parameters
folder_gform = "10qznFfdxwMXLaty5dqEkFTPoJfdwlGS3"  # Folder that contains all Google Forms
logging_level = 'DEBUG'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(message)s', level=logging_level, logger=logger)


# Pydrive auth
# TODO: no need to use pydrive (can do the same thing with google API)
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

# Google API auth
SCOPES = ["https://www.googleapis.com/auth/forms.body.readonly",
          "https://www.googleapis.com/auth/forms.responses.readonly"]
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
store = file.Storage('token.json')
creds = None
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = discovery.build('forms', 'v1', http=creds.authorize(
    Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

# Initialize dataframe to be exported as CSV
df = pd.DataFrame()

# Auto-iterate through all files that matches this query
drive = GoogleDrive(gauth)
file_list = drive.ListFile({'q': "'{}' in parents".format(folder_gform)}).GetList()
for file1 in file_list:
    form_id = file1['id']
    logger.debug('title: {}, id: {}'.format(file1['title'], form_id))
    # Get form metadata to get students' name
    result_metadata = service.forms().get(formId=form_id).execute()
    students = result_metadata['info']['title'].strip('Étudiants : ')
    # Get form responses
    result = service.forms().responses().list(formId=form_id).execute()
    len_result = len(result['responses'])
    gradeStudent = []
    for i_response in range(len_result):
        value = []
        matricule = ''
        for i, j in result['responses'][i_response]['answers'].items():
            result_item = j['textAnswers']['answers'][0]['value']
            # Hack: because results are not sorted (ie: matricule is not the first item), we need to look for the
            # matricule based on its properties: digit and length of 7.
            if len(result_item) == 7 and result_item.isdigit():
                matricule = result_item
            elif result_item.isdigit():
                value.append(result_item)
            else:
                logger.debug(f"Comment: {result_item}")
        # Make sure a matricule was found
        if matricule == '':
            raise RuntimeError('Problem identifying matricule.')
        grade = np.sum([int(i) for i in value])
        logger.debug('Matricule: {} | Grade: {}'.format(matricule, grade))
        if (matricule == '000000'):
            # Prof response
            gradeProf = grade
        else:
            # Student response
            gradeStudent.append(grade)
    # Compute average grade
    gradeAvg = (gradeProf + np.mean(gradeStudent)) / 2
    logger.info('grade: {}'.format(gradeAvg))
    # Append to dataframe
    df = pd.concat([df, pd.DataFrame({"Students": students, "Grade": gradeAvg}, index=[1])])

df.to_csv('grades_oral.csv')
