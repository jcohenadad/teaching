# Utility file for teaching library

import logging
import pandas as pd


# Initialize colored logging
# Note: coloredlogs.install() replaces logging.BasicConfig()
logger = logging.getLogger(__name__)


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

    # Loop across responses and fill Panda dataframe
    len_result = len(results['responses'])
    # gradeStudent = []
    responses_list = []
    for i_response in range(len_result):
        responses_dict = {}
        value = []
        matricule = ''
        is_prof = False
        for question_id, response_item in results['responses'][i_response]['answers'].items():
            result_item = response_item['textAnswers']['answers'][0]['value']
            question = question_lookup[question_id]
            responses_dict[question] = result_item
        responses_list.append(responses_dict)

    df = pd.DataFrame(responses_list)

    # Order columns based on the question_lookup order
    ordered_columns = [question_lookup[question_id] for question_id in question_lookup]
    df = df[ordered_columns]
    
    return df