# teaching

Collection of scripts to help organize teaching activities (create grading forms, send grades to students, etc.).

Some scripts require Google OAuth2.0 authentication. As a prerequisite, do this:
https://pythonhosted.org/PyDrive/quickstart.html#authentication
 
# Prerequisite (Google API)

- Enable [Google Forms API](https://console.developers.google.com/apis/api/forms.googleapis.com/overview?project=1036953068115)
- Enable [Gmail API](https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=1036953068115)

# Virtual environment

~~~
source activate teaching
~~~

# Install

~~~
pip install -e .
~~~

# Usage

## GBM6904/7904

- **Send feedback to student:** Go to Google Sheet that lists all presenters, fetch the required data and run:  
  ~~~
  send_feedback <MATRICULE> <URL>
  ~~~
  
