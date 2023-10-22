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