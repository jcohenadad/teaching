#!/usr/bin/env python
#
# For course GBM6125. Fetch Google Form (providing ID of the form), gather and email feedback to the student.
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

from utils.utils import fetch_responses, expand_url, gmail_send_message, fetch_email_address


# Parameters
FOLDER_ID = '17gfs6G0cSuKFG0UC3uFoEse6xC4hISGA'  # ID of the folder that includes all the gforms
SPREADSHEET_ID = '1ehztiWcQ8sIfktejWvxrHMYZpeDamqcrrWboy-Ha2oA'  # Google sheet that lists the matricules and URLs to the gforms
GSHEET_COLUMN_URL = 2  # column corresponding to the gform URL (starts at 0)
GSHEET_COLUMN_MATRICULE = 5  # column corresponding to the matricule
GSHEET_COLUMN_MATRICULE2 = 8  # column corresponding to the matricule of the 2nd student
MATRICULE_ID = 0  # ID of the question corresponding to the matricule
FEEDBACK_ID = 11  # ID of the question corresponding to the feedback
MATRICULE_JULIEN = '000000'
# TODO: have the address below in local config files
EMAIL_FROM = "jcohen@polymtl.ca"
PATH_CSV = "/Users/julien/Dropbox/documents/cours/GBM6904_seminaires/2023/GBM6904-7904-20233-01C.csv"
LOGGING_LEVEL = 'INFO'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)
coloredlogs.install(fmt='%(message)s', level=LOGGING_LEVEL, logger=logger)


def get_parameters():
    parser = argparse.ArgumentParser(description="""
    Fetch Google Form (providing ID of the form), gather and email feedback to the student.""")
    parser.add_argument('matricule',
                        help="Student matricule. Used to fetch the email address.")
    args = parser.parse_args()
    return args


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
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='Sheet1').execute()
    values = result.get('values', [])
    gform_url = None
    for row in values:
        if row[GSHEET_COLUMN_MATRICULE] == matricule:
            gform_url = row[GSHEET_COLUMN_URL]
            matricule2 = row[GSHEET_COLUMN_MATRICULE2]
            break
    if gform_url is not None:
        logger.info(f"Found gform URL: {gform_url}")
    else:
        raise RuntimeError('Did not find matching gform URL.')

    # Get expanded URL from shorten URL (listed in gsheet)
    gform_url_expanded = expand_url(gform_url)

    results = drive_service.files().list(q=f"'{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.form'",
                                        fields="files(id, name)").execute()
    items = results.get('files', [])

    logger.info("Fetching the associated Google Form edit URL...")
    # TODO replace with function
    gform_id = ''
    for item in items:
        # Fetch form details using the Forms API
        form_details = forms_service.forms().get(formId=item['id']).execute()
        # Extract the viewform URL
        viewform_url = form_details['responderUri']
        # Check if it corresponds to the target URL
        if viewform_url == gform_url_expanded:
            gform_id = item['id']
            logger.info(f"Found matched gform ID: {gform_id}")
    if gform_id == '':
        raise RuntimeError('Did not find matching edit URL.')
    # gform_id = "1Bfn5PwXRnk8sMNgV2I_n7-KBYB-FQ8EMuoEeLb6r1s0"  # DEBUG JULIEN

    # Get form metadata
    result_metadata = forms_service.forms().get(formId=gform_id).execute()

    # Get form responses
    results = forms_service.forms().responses().list(formId=gform_id).execute()

    df, ordered_columns = fetch_responses(results=results, result_metadata=result_metadata)

    # Compute average grade for each response
    # ---------------------------------------
    # Extract columns corresponding to graded questions
    subset_df = df[ordered_columns[1:6]]
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
        matricule_series = df.iloc[:, MATRICULE_ID]  # Assuming you have a matricule_column_name defined above
        # Extracting just the response value from matricule_series
        matricule_response_series = matricule_series.apply(lambda x: x['response'] if isinstance(x, dict) else None)
        # Compute the average for Julien's rows
        julien_avg = response_series[matricule_response_series == MATRICULE_JULIEN].mean()
        # Compute the average for Students' rows
        student_avg = response_series[matricule_series != MATRICULE_JULIEN].mean()
        # Compute the weighted average
        weighted_avg = 0.5 * julien_avg + 0.5 * student_avg
        averages_list.append(f"{question}: {weighted_avg:.2f}/{max_score}")
    # TODO: move the code above to utils to be reused when grading

    # # Loop across all responses and append student's feedback
    # # -------------------------------------------------------
    # # Use iloc to extract feedback for the specific question by its index
    # feedback_series = df.iloc[:, FEEDBACK_ID].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    # matricule_series = df.iloc[:, MATRICULE_ID].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    # # Identify non-NaN indices in feedback_series
    # valid_indices = feedback_series.dropna().index
    # # Filter both series using valid indices
    # filtered_feedback_series = feedback_series.loc[valid_indices]
    # filtered_matricule_series = matricule_series.loc[valid_indices]
    # julien_feedback = []
    # other_feedback = []
    # for feedback_value, matricule_value in zip(filtered_feedback_series, filtered_matricule_series):
    #     if matricule_value == MATRICULE_JULIEN:
    #         julien_feedback.append(feedback_value)
    #     else:
    #         other_feedback.append(feedback_value)
    # # Combine feedback: Julien's feedback at the top
    # feedback = julien_feedback + other_feedback

    # Indicate the number of students who responded (to check inconsistencies with the number of students in the class)
    logger.warning(f"\nNumber of responses: {len(results['responses'])}\n")

    # Fetch the matricule of the other student


    # Email feedback to student
    email_to = fetch_email_address(matricule, PATH_CSV)
    email_subject = '[GBM6904/7904] Feedback sur ta présentation orale'
    email_body = (
        f"Bonjour,\n\n"
        "Voici le résultat de la présentation que tu as donnée dans le cadre du cours GBM6904/7904.\n\n"
        "Voici tes notes par critère:\n\n" + "\n".join(averages_list) + "\n\n"
        # "Et voici le feedback de l'enseignant suivi du feedback des étudiants:\n\n" + "- " + "\n- ".join(feedback)
    )
    # email_body += "- " + "\n- ".join(feedback)
    # Printout message in Terminal and ask for confirmation before sending
    logger.info(f"\nEmail to send:\n\n {email_body}")
    send_prompt = input("Press [ENTER] to send, or type any text and then press [ENTER] to cancel.")
    if send_prompt == "":
        print("Message sent!")
        gmail_send_message(email_to, email_subject, email_body, creds)
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()
