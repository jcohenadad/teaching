#!/usr/bin/env python
#
# For course GBM6904. Fetch Google Form (providing ID of the form), gather and email feedback to the student.
#
# How to use:
# - Open the gsheet with the list of presentations
# - Open the URL of the gform for the student to send the feedback to
# - On the gform, click "edit", and then copy the new URL of the gform.
# - Run this function using that URL
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
import csv
import logging
import base64
import numpy as np
import os
import pandas as pd
import pickle
from email.message import EmailMessage

import coloredlogs

from requests import get
from oauth2client import client, file, tools
from google.auth.transport import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.utils import fetch_responses


# Parameters
folder_id = '1rj6GfMvK6_cirTHPYpExSPJtZHne-gM3'  # ID of the folder that includes all the gforms
SPREADSHEET_ID = '11vpuK2iiuIpUscjfI-Ork9fg0BzU3OFzuG9_-aweEDY'  # Google sheet that lists the matricules and URLs to the gforms
matriculeId = 0  # ID of the question corresponding to the matricule
matriculeJulien = '000000'
feedbackId = 11  # ID of the question corresponding to the feedback
# TODO: have the address below in local config files
email_from = "jcohen@polymtl.ca"
path_csv = "/Users/julien/Dropbox/documents/cours/GBM6904_seminaires/2023/GBM6904-7904-20233-01C.csv"
logging_level = 'INFO'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(message)s', level=logging_level, logger=logger)


def get_parameters():
    parser = argparse.ArgumentParser(description="""
    Fetch Google Form (providing ID of the form), gather and email feedback to the student.""")
    parser.add_argument('matricule',
                        help="Student matricule. Used to fetch the email address.")
    args = parser.parse_args()
    return args


def expand_url(short_url):
    """Expand URL from short URL

    Args:
        short_url (str): Short URL

    Returns:
        str: Long URL
    """
    # Follow the shortened URL to its destination
    response = get(short_url, allow_redirects=True, timeout=10)
    return response.url

    # Compute average grade
    gradeStudentAvg = np.mean(gradeStudent)
    gradeAvg = (gradeProf + gradeStudentAvg) / 2
    logger.info(f"grade: {gradeAvg} (StudentAvg: {gradeStudentAvg}, Prof: {gradeProf})")


def main():
    """
    :param args:
    :return:
    """

    # Get input parameters
    args = get_parameters()
    matricule = args.matricule

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/forms",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/gmail.send"
    ]

    creds = None

    # Check if the token.pickle file exists. If so, load it
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            request = requests.Request()
            creds.refresh(request)
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            # Open a browser window for authentication
            creds = flow.run_local_server(port=8080)

        # Save the credentials for future runs
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Build the forms_service objects for both APIs
    drive_service = build('drive', 'v3', credentials=creds)
    forms_service = build('forms', 'v1', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    # Find the gform URL from the Matricule on the gsheet
    INPUT_COLUMN_INDEX = 1  # column corresponding to the matricule (starts at 0)
    OUTPUT_COLUMN_INDEX = 5  # column corresponding to the gform URL
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1').execute()
    values = result.get('values', [])
    gform_url = None
    for row in values:
        if row[INPUT_COLUMN_INDEX] == matricule:
            gform_url = row[OUTPUT_COLUMN_INDEX]
            break
    if gform_url is not None:
        logger.info(f"Found gform URL: {gform_url}")
    else:
        raise RuntimeError('Did not find matching gform URL.')

    # Get expanded URL from shorten URL (listed in gsheet)
    gform_url_expanded = expand_url(gform_url)

    results = drive_service.files().list(q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.form'",
                                        fields="files(id, name)").execute()
    items = results.get('files', [])

    logger.info("Fetching the associated Google Form edit URL...")
    # TODO replace with function
    # gform_id = ''
    # for item in items:
    #     # Fetch form details using the Forms API
    #     form_details = forms_service.forms().get(formId=item['id']).execute()
    #     # Extract the viewform URL
    #     viewform_url = form_details['responderUri']
    #     # Check if it corresponds to the target URL
    #     if viewform_url == gform_url_expanded:
    #         gform_id = item['id']
    #         logger.info(f"Found matched gform ID: {gform_id}")
    # if gform_id == '':
    #     raise RuntimeError('Did not find matching edit URL.')
    gform_id = "1Bfn5PwXRnk8sMNgV2I_n7-KBYB-FQ8EMuoEeLb6r1s0"  # DEBUG JULIEN

    # Get form metadata
    result_metadata = forms_service.forms().get(formId=gform_id).execute()
    # student = result_metadata['info']['title']

    # # Get questionID of the feedback
    # questionId = ''
    # for item in result_metadata['items']:
    #     if item['title'] == title_feedback:
    #         questionId = item['questionItem']['question']['questionId']
    # if questionId == '':
    #     logger.error('questionId could not be retrieved. Check question title.')
    #     raise RuntimeError

    # # Get matriculeID of the evaluator
    # matriculeId = ''
    # for item in result_metadata['items']:
    #     logger.debug(item['title'])
    #     if item['title'] == 'Votre matricule étudiant :':
    #         matriculeId = item['questionItem']['question']['questionId']
    # if matriculeId == '':
    #     logger.warning('Problem identifying matricule.')

    # Get form responses
    results = forms_service.forms().responses().list(formId=gform_id).execute()

    df, ordered_columns = fetch_responses(results=results, result_metadata=result_metadata)

    # Compute average grade for each response
    # ---------------------------------------
    # Extract columns corresponding to graded questions
    subset_df = df[ordered_columns[1:10]]
    averages_list = []
    # Print out the questions and their averages
    for question in subset_df.columns:
        # Extracting the response and max score values from the nested dictionaries
        response_series = df[question].apply(lambda x: float(x['response']) if pd.notnull(x) else np.nan).dropna()
        max_score_series = df[question].apply(lambda x: x['max_score'] if pd.notnull(x) else np.nan).dropna()
        # Since all max scores for a particular question should be the same, 
        # just fetch the first value for the max score of this question
        max_score = max_score_series.iloc[0] if not max_score_series.empty else None
        # If we couldn't find a max score, default to 5 (or you can handle this differently)
        if max_score is None:
            raise ValueError(f"Max score not found for question: '{question}'")
        # Fetch all matricule rows
        matricule_series = df.iloc[:, matriculeId]  # Assuming you have a matricule_column_name defined above
        # Extracting just the response value from matricule_series
        matricule_response_series = matricule_series.apply(lambda x: x['response'] if isinstance(x, dict) else None)
        # Compute the average for Julien's rows
        julien_avg = response_series[matricule_response_series == matriculeJulien].mean()
        # Compute the average for Students' rows
        student_avg = response_series[matricule_series != matriculeJulien].mean()
        # Compute the weighted average
        weighted_avg = 0.5 * julien_avg + 0.5 * student_avg
        averages_list.append(f"{question}: {weighted_avg:.2f}/{max_score}")
    # TODO: move the code above to utils to be reused when grading

    # Loop across all responses and append student's feedback
    # -------------------------------------------------------
    # Use iloc to extract feedback for the specific question by its index
    feedback_series = df.iloc[:, feedbackId].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    matricule_series = df.iloc[:, matriculeId].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    # Identify non-NaN indices in feedback_series
    valid_indices = feedback_series.dropna().index
    # Filter both series using valid indices
    filtered_feedback_series = feedback_series.loc[valid_indices]
    filtered_matricule_series = matricule_series.loc[valid_indices]
    julien_feedback = []
    other_feedback = []
    for feedback_value, matricule_value in zip(filtered_feedback_series, filtered_matricule_series):
        if matricule_value == matriculeJulien:
            julien_feedback.append(feedback_value)
        else:
            other_feedback.append(feedback_value)
    # Combine feedback: Julien's feedback at the top
    feedback = julien_feedback + other_feedback

    # Indicate the number of students who responded (to check inconsistencies with the number of students in the class)
    logger.warning(f"\nNumber of responses: {len(results['responses'])}\n")

    # Email feedback to student
    email_to = fetch_email_address(matricule, path_csv)
    email_subject = '[GBM6904/7904] Feedback sur ta présentation orale'
    email_body = (
        f"Bonjour,\n\n"
        "Voici le résultat de la présentation que tu as donnée dans le cadre du cours GBM6904/7904.\n\n"
        "Voici tes notes par critère:\n\n" + "\n".join(averages_list) + "\n\n"
        "Et voici le feedback de l'enseignant suivi du feedback des étudiants:\n\n" + "- " + "\n- ".join(feedback)
    )
    # email_body += "- " + "\n- ".join(feedback)
    # Printout message in Terminal and ask for confirmation before sending
    logger.info('\nEmail to send:' + email_body)
    send_prompt = input("Press [ENTER] to send, or type any text and then press [ENTER] to cancel.")
    if send_prompt == "":
        print("Message sent!")
        gmail_send_message(email_to, email_subject, email_body, creds)
    else:
        print("Cancelled.")


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


def gmail_send_message(email_to: str, subject: str, email_body: str, creds):
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
    # TODO: do the authentication with the code above (to avoid doing it twice)
    # SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
    # store = file.Storage('token.json')
    # creds = None
    # if not creds or creds.invalid:
    #     flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    #     # tools is using args, therefore the workaround below creates a dummy parser with the mandatory flags
    #     # https://stackoverflow.com/questions/46737536/unrecognized-arguments-using-oauth2-and-google-apis
    #     parser = argparse.ArgumentParser(
    #         description=__doc__,
    #         formatter_class=argparse.RawDescriptionHelpFormatter,
    #         parents=[tools.argparser])
    #     flags = parser.parse_args([])
    #     creds = tools.run_flow(flow, store, flags=flags)

    try:
        forms_service = build('gmail', 'v1', credentials=creds)
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
        send_message = (forms_service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


if __name__ == "__main__":
    main()
