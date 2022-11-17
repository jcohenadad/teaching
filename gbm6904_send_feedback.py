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


import logging
import numpy as np
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools


# Parameters
# TODO: make it an input param
gform_url = "https://forms.gle/FM9HdFzgNGybsEMi8"  # URL of the Google Form

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

# Get form metadata to get students' name
# TODO: that is not the ID-- find a way to get IF from URL
form_id = gform_url.strip('https://forms.gle/')
result_metadata = service.forms().get(form_id).execute()
students = result_metadata['info']['title'].strip('Étudiants : ').split(' & ')
# Get form responses
result = service.forms().responses().list(formId=form_id).execute()
value = []
gradeStudent = []
for i, j in result['responses'][1].get('answers').items():
    # TODO: get text
    value.append(j['textAnswers']['answers'][0]['value'])

# TODO: email text to student