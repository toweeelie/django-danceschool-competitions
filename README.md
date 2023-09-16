# django-danceschool-competitions
Competitions app for django-danceschool project

Tested to work with WSL2 on Win11 and VSCode.
It's better to prepare virtual environment for python packages:
      
      python3 -m venv ./venv 
      source venv/bin/activate
      pip install -r requirements.txt
  
Next step is to create new DB and superuser:
      
      ./manage.py migrate
      ./manage.py createsuperuser
  
To run project it's enough to press F5 in VSCode, or to execute:
      
      ./manage.py runserver
