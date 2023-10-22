# Utility file for teaching library

import logging
import pandas as pd

from requests import get


# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)



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


def fetch_responses(results, result_metadata):

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
    len_result = len(results['responses'])
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
        message['From'] = EMAIL_FROM
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