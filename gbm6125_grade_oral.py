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

# import requests
from pydrive.auth import GoogleAuth

gauth = GoogleAuth()
gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.


# Parameters to setup
folder_gform = "1DjaqpTOp1QAy042qlFBoCpTY3wDA8lZp"  # Folder that contains all Google Forms

gsheet = requests.get(f'{PUBLICATIONS}/export?format=xlsx')

# TODO: input

