#!/usr/bin/env python
#
# For course GBM6904. Fetch Google Form (providing ID of the form), gather and email feedback to the student.
#
# How to use:
# - Open the gsheet with the list of presentations
# - Copy the URL of the student to send the feedback to
# - Input in this function
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

from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


# Parameters
# TODO: make it an input param
# folder_gform = '10qznFfdxwMXLaty5dqEkFTPoJfdwlGS3'  # Folder ID that contains all Google Forms
gform_url = "https://docs.google.com/forms/d/1i6plhhhnYtP-qHnstB1yBLusKdDdy05rXmJX0Lj8jro/viewform"  # URL of the Form
logging_level = 'DEBUG'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(message)s', level=logging_level, logger=logger)

# Pydrive auth
# TODO: no need to use pydrive (can do the same thing with google API)
# gauth = GoogleAuth()
# gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

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

# Get ID from URL
gform_id = gform_url.removeprefix('https://docs.google.com/forms/d/').removesuffix('/viewform')

# Get form metadata to get students' name
result_metadata = service.forms().get(formId=gform_id).execute()
student = result_metadata['info']['title']
# Get form responses
result = service.forms().responses().list(formId=gform_id).execute()
feedback = []
for i, j in result['responses'][1].get('answers').items():
    # TODO: get text
    feedback.append(j['textAnswers']['answers'][0]['value'])

# TODO: email text to student