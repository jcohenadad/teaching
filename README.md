# teaching

Collection of scripts to help organize teaching activities (create grading forms, send grades to students, etc.).

Some scripts require Google OAuth2.0 authentication. As a prerequisite, do this:
https://pythonhosted.org/PyDrive/quickstart.html#authentication
 
# Prerequisite (Google API)

- Enable [Google Forms API](https://console.developers.google.com/apis/api/forms.googleapis.com/overview?project=1036953068115)
- Enable [Gmail API](https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=1036953068115)
- [Download your OAuth 2.0 Client ID JSON from Google Cloud Console](https://console.cloud.google.com/apis/dashboard) and place it at the root of the repository (ie: where the file `setup.py` is located).


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

# Usage

## GBM6904/7904

- **Send feedback to student:** Go to Google Sheet that lists all presenters, fetch the required data and run:  
  ~~~
  send_feedback
  ~~~

## GBM6125

[Send feedback to students](https://github.com/jcohenadad/teaching/blob/16bc379bcb0b2f71a1ede707fb0519a52ca3f17e/teaching/gbm6125_send_feedback.py#L6)

### Generate CSV with oral grades

For batch run across all students, first, go to the Gsheet and convert the column of matricule into a space-separated list using:
~~~
=JOIN(" ", F2:F14) (replace F2:F14 with the appropriate cells)
~~~

Then, in the Terminal, run:

~~~
source venv/bin/activate
matricules="<PASTE_ALL_MATRICULES_HERE>"
for matricule in $matricules; do gbm6125_send_feedback "$matricule" --compute-grade notes_oral.csv; done
~~~
