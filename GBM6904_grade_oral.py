# -*- coding: latin-1 -*-

#to do : download csv files directly from Gdrive
# Developed by: Alexandru Foias
# 2018-11-06

import csv
import argparse
import os


class bcolors:
    normal = '\033[0m'
    red = '\033[91m'  # red
    green = '\033[92m'  # green
    yellow = '\033[93m' #yellow
    cyan = '\033[96m' #cyan

def get_parameters():
    parser = argparse.ArgumentParser(description='This script is used for'
        'computing the grades for oral GBM6904')
    parser.add_argument("-c", "--csv",
                        help="Path to csv response file",
                        required=True)
    args = parser.parse_args()
    return args

def main(path_csv):
    """
    Main function
    :param path_csv:
    :return:
    """
    
    final_grade_weight = 20
    max_grade = 50


    output_csv = []
    buffer_output = []
    csv_row = 0

    file_csv = open(path_csv, 'rb')
    reader_csv = csv.reader(file_csv)
    buffer_csv = []
    for row in reader_csv:
        buffer_csv.append(row)
    file_csv.close()
    print ('\n')
    
    path_csv_class = '/Users/alfoi/Desktop/work/teaching/data_gbm6904/GBM6904_2019.csv'
    file_csv_class = open(path_csv_class, 'rb')
    reader_csv = csv.reader(file_csv_class)
    buffer_csv_class = []
    for row in reader_csv:
        buffer_csv_class.append(row)
    file_csv_class.close()
    buffer_class_ids = []
    for row_id in range (1,len(buffer_csv_class)):
        buffer_class_ids.append(buffer_csv_class[row_id][0])

        
    print ('\nNo of feedbacks: ' + str(len(buffer_csv)-1))
    sum_grade_students = 0
    students_count = 0
    buffer_answer_name = []
    buffer_feedback = []
    for row_id in range (1,len(buffer_csv)):
        if buffer_csv[row_id][1] in buffer_answer_name:
            print (bcolors.yellow +'Warning duplicate: ' + bcolors.green + str(row_id+1) + bcolors.normal + ' ' + bcolors.red + buffer_csv[row_id][1] + bcolors.normal)
        else:
            # print 'Okay for : ' + bcolors.green + buffer_csv[row_id][1] + bcolors.normal
            line_sum = 0
            for column_id in range (2,len(buffer_csv[row_id])-1):
                line_sum += int(buffer_csv[row_id][column_id])
            if buffer_csv[row_id][1] == '101317':
                # print bcolors.yellow + 'Found Julien' + bcolors.normal
                avg_prof = float(line_sum) 
            else:
                sum_grade_students += line_sum
                students_count +=1

        if buffer_csv[row_id][len(buffer_csv[row_id])-1] != "":    
            buffer_feedback.append(buffer_csv[row_id][len(buffer_csv[row_id])-1])
        buffer_answer_name.append(buffer_csv[row_id][1])
    avg_students = sum_grade_students/float(students_count)

    final_grade = (avg_prof + avg_students)/2
    print ('No. of students: ' + bcolors.green + str(students_count) + bcolors.normal)
    print ('Grade teacher: ' + bcolors.green + str(avg_prof) + bcolors.normal)
    print ('Grade students: ' + bcolors.green + str(avg_students) + bcolors.normal)
    print (bcolors.yellow + 'Interm grade: ' + bcolors.green + str(final_grade) + bcolors.normal)
    buffer_final_grade_rescaled = final_grade * 100/max_grade #compute percentage out of max grade
    final_grade_rescaled = buffer_final_grade_rescaled * final_grade_weight/100 # final grade weighted
    print ('\n')
    print (bcolors.red + 'Final grade : ' + bcolors.cyan + str(final_grade_rescaled) + bcolors.normal)
    print ('\n')

    print ('Email subject: 	[GBM6904/7904] - Feedback pour la présentation orale/ Feedback on your oral presentation \n')
    print ("""Email body: 
    
    Bonjour,
    Voici le feedback pour votre présentation orale.

    Hi,
    Here is the feedback on your oral presentation.
    """)
    for id_feedback in buffer_feedback:
        print ('• ' + id_feedback)
    
    print ("""
    Cordialement,
    Alexandru
    --
    Alexandru Foias MScA
    
    Research Associate, HQP TransMedTech
    Department of Electrical Engineering, Polytechnique Montréal
    2900 Edouard-Montpetit Bld, room L-5626
    Montreal, QC, H3T1J4, Canada
    Phone: +1 (514) 340-4711 (office: 7546) 
    E-mail: alexandru.foias@polymtl.ca
    Web: www.neuro.polymtl.ca""")
    print ("""\nLet's check if we have any absents: """)
    print (list(set(buffer_class_ids) - set(buffer_answer_name)))

if __name__ == "__main__":
    args = get_parameters()
    main(args.csv)
