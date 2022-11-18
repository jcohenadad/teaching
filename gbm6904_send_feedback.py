#!/usr/bin/env python
#
# For course GBM6904. Fetch Google Form (providing ID of the form), gather and email feedback to the student.
#
# The file "client_secrets.json" need to be present in the working directory.
#
# Useful documentation
# - https://developers.google.com/drive/api/guides/search-files
# - https://developers.google.com/forms/api/guides/retrieve-forms-responses?hl=en
# - https://pythonhosted.org/PyDrive/quickstart.html#authentication
#
# Author: Julien Cohen-Adad
#
# TODO: change script to function


import coloredlogs
import logging
import numpy as np
# import google.auth
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


# Parameters
# TODO: make it an input param
folder_gform = '10qznFfdxwMXLaty5dqEkFTPoJfdwlGS3'  # Folder ID that contains all Google Forms
gform_id = "https://docs.google.com/forms/d/e/1FAIpQLSfBNS4_2lz4Vj199lc9wtR51XYsjq0PDCqSShYcUHQk7G46aA/viewform"  # ID of the Google Form. Find it by clicking on the URL that brings to the form.
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

# Iterate through all files in folder
drive = GoogleDrive(gauth)
file_list = drive.ListFile({'q': "'{}' in parents".format(folder_gform)}).GetList()
for file1 in file_list:
    form_id = file1['id']
    logger.debug('title: %s, id: %s' % (file1['title'], form_id))


service = discovery.build('drive', 'v1', http=creds.authorize(
    Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

response = service.files().list(q="'{}' in parents".format('GBM6904-2022_GoogleForms'),
                                spaces='drive',
                                fields='nextPageToken, '
                                       'files(id, name)').execute()

for file in response.get('files', []):
    # Process change
    print(F'Found file: {file.get("name")}, {file.get("id")}')
files.extend(response.get('files', []))
page_token = response.get('nextPageToken', None)
# if page_token is None:
#
# service = discovery.build('forms', 'v1', http=creds.authorize(
#     Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)


# creds, _ = google.auth.default()

try:
    # create drive api client
    # service = build('drive', 'v3', credentials=creds)
    # files = []
    # page_token = None
    while True:
        # pylint: disable=maybe-no-member
        response = service.files().list(q="mimeType='form'",
                                        spaces='drive',
                                        fields='nextPageToken, '
                                               'files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            print(F'Found file: {file.get("name")}, {file.get("id")}')
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
except HttpError as error:
    print(F'An error occurred: {error}')
    files = None


# Get form metadata to get students' name
result_metadata = service.forms().get(formId=gform_id).execute()
students = result_metadata['info']['title'].strip('Étudiants : ').split(' & ')
# Get form responses
result = service.forms().responses().list(formId=gform_id).execute()
value = []
gradeStudent = []
for i, j in result['responses'][1].get('answers').items():
    # TODO: get text
    value.append(j['textAnswers']['answers'][0]['value'])

# TODO: email text to student