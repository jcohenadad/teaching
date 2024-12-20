#!/usr/bin/env python
#
# For course GBM6904. Fetch Google Form (providing ID of the form), gather and email feedback to the student.
#
# How to use:
# - Make sure the Parameters (below) are set correctly
# - Open the gsheet with the list of presentations
# - Copy the matricule of the first presenting student
# - Run this function: 
#   > python teaching/gbm6904_send_feedback.py <MATRICULE>
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
import logging
import numpy as np
import os
import pandas as pd
import pickle

import coloredlogs

from requests import get
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from teaching.utils.utils import fetch_responses, expand_url, gmail_send_message, fetch_email_address, compute_weighted_averages


# Parameters
FOLDER_ID = '1I7S-RHJ9WgQAGa51RuVmRhe2sddHPrqa'  # ID of the Google folder that includes all the gforms (go to the folder, click on "Open in new window", and copy the ID from the URL)
SPREADSHEET_ID = '1fOREGH2EFc1gxTDMrMwmhjX-QBk20BvqncugHvy85lE'  # Google sheet that lists the matricules and URLs to the gforms
PATH_CSV = "/Users/julien/Library/CloudStorage/Dropbox/documents/cours/GBM6904_seminaires/2024/GBM6904-20243-01C.CSV"  # Path to the CSV file that links matricule to email address
MATRICULE_ID = 0  # ID of the question corresponding to the matricule
MATRICULE_JULIEN = '000000'
FEEDBACK_ID = 11  # ID of the question corresponding to the feedback
# TODO: have the address below in local config files
EMAIL_FROM = "jcohen@polymtl.ca"
LOGGING_LEVEL = 'INFO'  # 'DEBUG', 'INFO'

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(name="teaching")
coloredlogs.install(fmt='%(message)s', level=LOGGING_LEVEL, logger=logger)


def get_parameters():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=
    "Fetch Google Form (providing ID of the form), gather and email feedback to the student.\n\n"
    "For batch run across all students, first, go to the Gsheet and convert the column of matricule into a space-separated list using:\n"
    "> '=JOIN(\" \", F2:F14)' (replace F2:F14 with the appropriate cells)\n"
    "Then, in the Terminal, run:\n"
    "> matricules=MATRICULE1 MATRICULE2 MATRICULE3 ...\n"
    "> for matricule in $matricules; do gbm6904_send_feedback $matricule --compute-grade oral.csv; done\n"
    )
    parser.add_argument('matricule',
                        help="Student matricule. Used to fetch the email address.")
    parser.add_argument('--compute-grade', type=str, default=None,
                        help='Compute the grade (/20) and store it in a CSV file specified by this argument. Append to the CSV file if it already exists. When this argument is called, feedback is not sent to the student.')
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
    compute_grade = args.compute_grade

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/forms",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/gmail.send"
    ]

    creds = None

    # Check if the token.pickle file exists. If so, load it
    token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                print("Refresh token is invalid or expired. Deleting token.pickle and re-authenticating...")
                os.remove(token_path)  # Delete the invalid token
                flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
                creds = flow.run_local_server(port=8080)
        else:
            print("No valid credentials found. Re-authenticating...")
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save the credentials for future runs
        with open(token_path, 'wb') as token:
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
        logger.error(f"Did not find matching gform URL for matricule={matricule}.")
        raise RuntimeError("Did not find matching gform URL.")

    # Get expanded URL from shorten URL (listed in gsheet)
    gform_url_expanded = expand_url(gform_url)

    # Remove query parameters from the URL
    gform_url_expanded = gform_url_expanded.split('?')[0]
    logger.info(f"Expanded URL: {gform_url_expanded}")

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
        logger.error(f"Did not find matching edit URL for matricule={matricule}.")
        raise RuntimeError('Did not find matching edit URL.')
    # gform_id = "1Bfn5PwXRnk8sMNgV2I_n7-KBYB-FQ8EMuoEeLb6r1s0"  # DEBUG JULIEN

    # Get form metadata
    result_metadata = forms_service.forms().get(formId=gform_id).execute()

    # Get form responses
    results = forms_service.forms().responses().list(formId=gform_id).execute()
    df, ordered_columns = fetch_responses(results=results, result_metadata=result_metadata, matricule=matricule)

    # Compute average grade for each response
    averages_list, weighted_avg_sum = compute_weighted_averages(df, ordered_columns, 1, 10, MATRICULE_ID, MATRICULE_JULIEN, matricule)

    # Compute grade and store it in a CSV file
    if compute_grade:
        # Check if the file exists, and if it does not, add header 'matricule;note'
        if not os.path.exists(compute_grade):
            with open(compute_grade, 'w') as f:
                f.write('matricule;note\n')
        # Append to CSV file
        average_grade = f"{matricule};{weighted_avg_sum:.2f}"
        with open(compute_grade, 'a') as f:
            f.write(average_grade + '\n')
        logger.info(f"Grade saved in {compute_grade}")
        return

    # ---------------------------------------
    # Extract columns corresponding to graded questions
    subset_df = df[ordered_columns[1:11]]
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

    # Loop across all responses and append student's feedback
    # -------------------------------------------------------
    # Use iloc to extract feedback for the specific question by its index
    feedback_series = df.iloc[:, FEEDBACK_ID].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    matricule_series = df.iloc[:, MATRICULE_ID].apply(lambda x: x['response'] if isinstance(x, dict) and 'response' in x else None)
    # Identify non-NaN indices in feedback_series
    valid_indices = feedback_series.dropna().index
    # Filter both series using valid indices
    filtered_feedback_series = feedback_series.loc[valid_indices]
    filtered_matricule_series = matricule_series.loc[valid_indices]
    julien_feedback = []
    other_feedback = []
    for feedback_value, matricule_value in zip(filtered_feedback_series, filtered_matricule_series):
        if matricule_value == MATRICULE_JULIEN:
            julien_feedback.append(feedback_value)
        else:
            other_feedback.append(feedback_value)
    # Combine feedback: Julien's feedback at the top
    feedback = julien_feedback + other_feedback

    # Indicate the number of students who responded (to check inconsistencies with the number of students in the class)
    logger.info(f"\nNumber of responses: {len(results['responses'])}\n")

    # Email feedback to student
    email_to = fetch_email_address(matricule, PATH_CSV)
    email_subject = '[GBM6904/7904] Feedback sur ta présentation orale'
    email_body = (
        f"Bonjour,\n\n"
        "Voici le résultat de la présentation que tu as donnée dans le cadre du cours GBM6904/7904.\n\n"
        "Voici tes notes par critère (pondération : 50% enseignant, 50% moyenne de la classe) :\n\n" + "\n".join(averages_list) + "\n\n"
        "Et voici le feedback de l'enseignant suivi du feedback des étudiants:\n\n" + "- " + "\n- ".join(feedback) + "\n\nJulien Cohen-Adad"
    )
    # Printout message in Terminal and ask for confirmation before sending
    logger.warning(f"Email to send (dest: {email_to}):\n\n{email_body}")
    send_prompt = input("Press [ENTER] to send, or type any text and then press [ENTER] to cancel.")
    if send_prompt == "":
        print("Message sent!")
        gmail_send_message(EMAIL_FROM, email_to, email_subject, email_body, creds)
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()
