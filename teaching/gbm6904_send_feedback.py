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

import argparse
import coloredlogs
import csv
import logging
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Parameters
title_feedback = "S'il vous plaît donnez un retour constructif à l'étudiant.e (anonyme)"  # title of the question (required to retrieve the questionId
# TODO: have the address below in local config files
email_from = "jcohen@polymtl.ca"
path_csv = "/Users/julien/Dropbox/documents/cours/GBM6904_seminaires/2022/GBM6904-7904-20223-01C.csv"
logging_level = 'DEBUG'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(message)s', level=logging_level, logger=logger)


def get_parameters():
    parser = argparse.ArgumentParser(description="""
    Fetch Google Form (providing ID of the form), gather and email feedback to the student.""")
    parser.add_argument("-u", "--url",
                        help="URL of the Google Form",
                        required=True)
    parser.add_argument("-m", "--matricule",
                        help="Student matricule. Used to fetch the email address.",
                        required=True)
    args = parser.parse_args()
    return args


def main():
    """
    :param args:
    :return:
    """

    # Get input parameters
    args = get_parameters()
    gform_url = args.url
    matricule = args.matricule

    # Google API auth
    SCOPES = ["https://www.googleapis.com/auth/forms.body.readonly",
              "https://www.googleapis.com/auth/forms.responses.readonly"]
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"
    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        # tools is using args, therefore the workaround below creates a dummy parser with the mandatory flags
        # https://stackoverflow.com/questions/46737536/unrecognized-arguments-using-oauth2-and-google-apis
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        # flags = parser.parse_args(['--client-id', '', '--client-secret', ''])
        flags = parser.parse_args([])
        creds = tools.run_flow(flow, store, flags=flags)
    service = discovery.build('forms', 'v1', http=creds.authorize(
        Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

    # Get ID from URL
    gform_id = gform_url.removeprefix('https://docs.google.com/forms/d/').removesuffix('/viewform')

    # Get form metadata to get students' name
    result_metadata = service.forms().get(formId=gform_id).execute()
    student = result_metadata['info']['title']
    # Get questionID of the feedback
    questionId = ''
    for item in result_metadata['items']:
        if item['title'] == title_feedback:
            questionId = item['questionItem']['question']['questionId']
    if questionId == '':
        logger.error('questionId could not be retrieved. Check question title.')
        raise RuntimeError

    # Get form responses
    result = service.forms().responses().list(formId=gform_id).execute()
    # Loop across all responses and append student's feedback
    feedback = []
    for responses in result['responses']:
        logger.debug(responses)
        if questionId in responses['answers'].keys():
            feedback.append(responses['answers'][questionId]['textAnswers']['answers'][0]['value'])

    # TODO: email text to student
    email_to = fetch_email_address(matricule, path_csv)
    email_subject = '[GBM6904/7904] Feedback sur ta présentation orale'
    email_body = \
        "Bonjour,\n\n" \
        "Voici le feedback de la présentation que tu as donnée dans le cadre du cours GBM6904/7904. Chaque item " \
        "ci-dessous correspond au feedback d'un étudiant.\n\n"
    email_body += "- " + "\n- ".join(feedback)
    gmail_send_message(email_to, email_subject, email_body)


def fetch_email_address(matricule: str, path_csv: str) -> str:
    """
    Find email address of student based on their matricule, using a CSV file that is provided by the university.
    This function assumes the following CSV structure:
        matricule | Last name | First name | email

    :param matricule:
    :param path_csv: CSV file that contains matricule and email address of students. Provided by the university.
    :return: email_addr: Email address of student
    """
    # encoding='latin-1' is required because of non utf-8 characters in the CSV file (accents, etc.)
    with open(path_csv, newline='', encoding='latin-1') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            if row[0] == matricule:
                return row[3]
        # If email was not found, raise error
        logger.error('Did not found email from the CSV file with matricule: {}'.format(matricule))
        raise RuntimeError


def gmail_send_message(email_to: str, subject: str, email_body: str):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    :param email_to: Recipient of the email
    :param subject: Subject of the email
    :param email_body: Body of the email
    :return:
    """
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    store = file.Storage('token.json')
    creds = None
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
        # tools is using args, therefore the workaround below creates a dummy parser with the mandatory flags
        # https://stackoverflow.com/questions/46737536/unrecognized-arguments-using-oauth2-and-google-apis
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[tools.argparser])
        flags = parser.parse_args([])
        creds = tools.run_flow(flow, store, flags=flags)

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(email_body)
        # TODO: fetch email_to automatically
        message['To'] = email_to
        message['From'] = email_from
        message['Subject'] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


if __name__ == "__main__":
    main()
