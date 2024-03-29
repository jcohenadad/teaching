# teaching

Collection of scripts to help organize teaching activities (create grading forms, send grades to students, etc.).

Some scripts require Google OAuth2.0 authentication. As a prerequisite, do this:
https://pythonhosted.org/PyDrive/quickstart.html#authentication
 
# Prerequisite (Google API)

- Enable [Google Forms API](https://console.developers.google.com/apis/api/forms.googleapis.com/overview?project=1036953068115)
- Enable [Gmail API](https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=1036953068115)

# GBM6904

Generate gforms with Google AppsScript: [GBM6904_CreateForm](https://script.google.com/home/projects/1a2_dd4s7rkh1ETUG5TwXsc5jJ1nKXg3aKT9zVfPIFoXhx5kJYpreA1Ry/edit)

# Virtual environment

~~~
source activate teaching
~~~

# Install

~~~
pip install -e .
~~~

Tips: add alias in your bashrc/zshrc (for Tab completion):
~~~
alias send_feedback="send_feedback"
~~~

# Usage

## GBM6904/7904

- **Send feedback to student:** Go to Google Sheet that lists all presenters, fetch the required data and run:  
  ~~~
  send_feedback <MATRICULE> <URL>
  ~~~
  
