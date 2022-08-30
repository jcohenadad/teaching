import smtplib
import csv
import os
import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
 
path_csv_file = "/Users/alfoi/Downloads/gbm6904_2018-10-24/GBM6904_2018_notes.csv"
path_abstract_dir = "/Users/alfoi/Downloads/gbm6904_2018-10-24/abstracts/"

fromaddr = "ADDR"
cc = "ADDR"
log_addr = "ADDR","ADDR"

### Read csv file 
file_csv = open(path_csv_file, 'rb')
reader_csv = csv.reader(file_csv)

buffer_csv = []
for row in reader_csv:
    buffer_csv.append(row)
file_csv.close()

email_log=[]
# Send emails

for email_no in range(1,len(buffer_csv)):
    toaddrs = []
    toaddr = buffer_csv[email_no][3]
    student_id = buffer_csv[email_no][0]

    toaddrs.append(cc)
    toaddrs.append(toaddr)
    print toaddrs

    msg = MIMEMultipart()
    
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddrs)
    msg['Subject'] = "FINAL TEST - [GBM6904/7904] - Correction abstract"
    
    body = """
    Bonjour,

    Veuillez trouver ci-joint votre abstract avec corrections.

    Cordialement,
    Alexandru Foias
    --
    Alexandru Foias MScA

    Research Associate
    Department of Electrical Engineering, Polytechnique Montreal
    2900 Edouard-Montpetit Bld, room L-5626
    Montreal, QC, H3T1J4, Canada
    Phone: +1 (514) 340-4711 (office: 7546) 
    E-mail: alexandru.foias@polymtl.ca
    Web: www.neuro.polymtl.ca
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    filename = 'ABSTRACT_' + str(student_id) + '_JCA.docx'
    path_attachment = path_abstract_dir + 'ABSTRACT_' + str(student_id) + '_JCA.docx'
    if os.path.isfile(path_attachment):
        attachment = open(path_attachment , "rb")
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.polymtl.ca', 587)
        text = msg.as_string()

        server.sendmail(fromaddr, toaddrs, text)
        server.quit()
        email_log.append('\n'+ str(datetime.datetime.now()) + ' -- Abstract sent for student id: ' + student_id + ' with email: ' + toaddr)
    else:
        email_log.append('\n'+ str(datetime.datetime.now()) + ' -- No abstract found for student id: ' + student_id + ' with email: ' + toaddr)

### Send email log
str_email_log = ''.join(email_log)
print str_email_log

msg = MIMEMultipart()
    
msg['From'] = fromaddr
msg['To'] = ", ".join(log_addr)
currentDT = datetime.datetime.now()

msg['Subject'] = "ABSTRACT LOG - [GBM6904/7904] - " + currentDT.strftime("%Y-%m-%d")
body = str_email_log
    
msg.attach(MIMEText(body, 'plain'))
    
server = smtplib.SMTP('smtp.polymtl.ca', 587)
text = msg.as_string()
server.sendmail(fromaddr, log_addr, text)
server.quit()
