# Utility file for teaching library

import logging

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
    
    for i_response in range(len_result):
        value = []
        matricule = ''
        is_prof = False
        for question_id, response_item in results['responses'][i_response]['answers'].items():
            result_item = response_item['textAnswers']['answers'][0]['value']
            question = question_lookup[question_id]

            


            result_item = j['textAnswers']['answers'][0]['value']
            # Hack: because results are not sorted (ie: matricule is not the first item), we need to look for the
            # matricule based on its properties: digit and length of 7.
            if result_item == '000000':
                # that's me :)
                matricule = result_item
                is_prof = True
            elif len(result_item) == 7 and result_item.isdigit():
                matricule = result_item
            elif result_item.isdigit():
                value.append(result_item)
            else:
                logger.debug(f"Comment: {result_item}")
        # Make sure a matricule was found
        if matricule == '':
            raise RuntimeError('Problem identifying matricule.')
        
        grade = np.sum([int(i) for i in value])
        logger.debug('Matricule: {} | Grade: {}'.format(matricule, grade))
        if is_prof:
            # Prof response
            gradeProf = grade
        else:
            # Student response
            gradeStudent.append(grade)