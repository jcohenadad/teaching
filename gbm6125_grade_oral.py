#!/usr/bin/env python
#
# Loop across Google Forms, fetch responses, analyze them and output average grade in a CSV file.
# Specific to the course GBM6125 at Polytechnique Montreal.
#
# Useful documentation
# - https://developers.google.com/drive/api/guides/search-files
# - https://developers.google.com/forms/api/guides/retrieve-forms-responses?hl=en
# - https://pythonhosted.org/PyDrive/quickstart.html#authentication
#
# Author: Julien Cohen-Adad

# Parameters
folder_gform = "1DjaqpTOp1QAy042qlFBoCpTY3wDA8lZp"  # Folder that contains all Google Forms

# import requests
import logging
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools


# Pydrive auth
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

# Google API auth
SCOPES = ["https://www.googleapis.com/auth/forms.body.readonly",
          "https://www.googleapis.com/auth/forms.responses.readonly"]
# SCOPES = "https://www.googleapis.com/auth/forms"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
store = file.Storage('token.json')
creds = None
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = discovery.build('forms', 'v1', http=creds.authorize(
    Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)


# Auto-iterate through all files that matches this query
drive = GoogleDrive(gauth)
file_list = drive.ListFile({'q': "'{}' in parents".format(folder_gform)}).GetList()
for file1 in file_list:
    form_id = file1['id']
    logging.debug('title: %s, id: %s' % (file1['title'], form_id))
    result_metadata = service.forms().get(formId=form_id).execute()
    students = result_metadata['info']['title'].strip('Étudiants : ').split(' & ')
    result = service.forms().responses().list(formId=form_id).execute()

#       grade = computeGrade(itemResponses);
#       Logger.log('Matricule: %s | Grade: %s', matricule, grade.toString());
#       if (matricule == "000000") {
#         // Prof response
#         var gradeProf = grade;
#       } else {
#         // Student response
#         gradeStudents.push(grade);
#       }
#     }
#     // Compute average grade
#     var gradeAverage = computeAverageGrade(gradeProf, gradeStudents);
#     // Logger.log('gradeStudents: %s', gradeStudents)
#     // TODO: put value in gsheet