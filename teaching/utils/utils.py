# Utility file for teaching library

import base64
import csv
import logging
import numpy as np
import pandas as pd

from requests import get
from email.message import EmailMessage
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger("teaching")


def compute_weighted_averages(df, ordered_columns, col_start, col_end, matricule_id, matricule_julien, matricule_student):
    """Compute the weighted average grade for each response. Outputs a list of strings with the 
    weighted average for each question, as well as the sum of the weighted averages, normalized to 20.

    Args:
        df (_type_): _description_
        ordered_columns (_type_): _description_
        col_start (_type_): _description_
        col_end (_type_): _description_
        matricule_id (_type_): _description_
        matricule_julien (_type_): _description_
        matricule_student (_type_): Matricule of the student to compute the weighted average for

    Returns:
        _type_: List of strings with the weighted average for each question
        _type_: Sum of the weighted averages, normalized to 20
    """    """"""
    # Extract columns corresponding to graded questions
    subset_df = df[ordered_columns[col_start:col_end]]
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
        matricule_series = df.iloc[:, matricule_id]

        # Extracting just the response value from matricule_series
        matricule_response_series = matricule_series.apply(lambda x: x['response'] if isinstance(x, dict) else None)

        # Compute the average for Julien's rows
        julien_avg = response_series[matricule_response_series == matricule_julien].mean()
        if np.isnan(julien_avg):
            logger.error(f"julien_avg is NaN for student: {matricule_student}")
            raise ValueError("julien_avg is NaN")

        # Compute the average for Students' rows
        student_avg = response_series[matricule_series != matricule_julien].mean()
        if np.isnan(student_avg):
            raise ValueError("student_avg is NaN")

        # Compute the weighted average
        weighted_avg = 0.5 * julien_avg + 0.5 * student_avg

        averages_list.append(f"{question}: {weighted_avg:.2f}/{max_score}")

    # Compute the sum of the weighted averages
    weighted_avg_sum = sum([float(x.split('/')[0].split(': ')[1]) for x in averages_list])
    # Normalize to a max score of 20, using the max grade for each question
    weighted_avg_sum = weighted_avg_sum / sum([float(x.split('/')[1]) for x in averages_list]) * 20

    return averages_list, weighted_avg_sum


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


def fetch_responses(results, result_metadata, matricule):

    # Get matriculeID of the evaluator
    matriculeId = ''
    for item in result_metadata['items']:
        logger.debug(item['title'])
        if item['title'] == 'Votre matricule étudiant :':
            matriculeId = item['questionItem']['question']['questionId']
    if matriculeId == '':
        logger.warning('Problem identifying matricule.')
    
    # Create a lookup dictionary for question IDs and their texts
    question_lookup = {item['questionItem']['question']['questionId']: item['title'] 
                   for item in result_metadata['items']}

    # Extracting the high value from scaleQuestion for each grading question
    max_score_lookup = {}
    for item in result_metadata['items']:
        question_id = item['questionItem']['question']['questionId']
        scale_question = item['questionItem']['question'].get('scaleQuestion')
        if scale_question:
            max_score_lookup[question_id] = scale_question.get('high', None)

    # Loop across responses and fill Panda dataframe
    try:
        len_result = len(results['responses'])
    except KeyError:
        logger.error(f"No responses found for student: {matricule}")
        raise RuntimeError
    # gradeStudent = []
    responses_list = []
    # max_scores_dict = {}
    for i_response in range(len_result):
        responses_dict = {}
        # max_scores_dict = {}
        # value = []
        # matricule = ''
        # is_prof = False
        for question_id, response_item in results['responses'][i_response]['answers'].items():
            result_item = response_item['textAnswers']['answers'][0]['value']
            question = question_lookup[question_id]
            max_score = max_score_lookup.get(question_id, None)
            responses_dict[question] = {'response': result_item, 'max_score': max_score}
            # # Here, also fetch the corresponding max_score for the question
            # if question_id in max_score_lookup:
            #     max_scores_dict[question + " Max Score"] = max_score_lookup[question_id]
        # Append both the responses and the max_scores to the responses_list
        # responses_dict.update(max_scores_dict)
        responses_list.append(responses_dict)
    
    df = pd.DataFrame(responses_list)

    # Order columns based on the question_lookup order
    ordered_columns = [question_lookup[question_id] for question_id in question_lookup]
    df = df[ordered_columns]

    return df, ordered_columns


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


def gmail_send_message(email_from: str, email_to: str, subject: str, email_body: str, creds):
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