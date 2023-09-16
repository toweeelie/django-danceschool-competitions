# django-danceschool-competitions
Competitions app for django-danceschool project

Tested to work with WSL2 (Ubuntu 22.04) on Win11. Installation steps:

1. It's better to prepare virtual environment for python packages:
      
            python3 -m venv ./venv 
            source venv/bin/activate

2. Dependencies installation may take some time, I tried to remove as much as possible, possibly I turned off some useful UI features:
      
            pip install -r requirements.txt
  
3. Next step is to create new DB and superuser:
      
            ./manage.py migrate
            ./manage.py createsuperuser
  
This should be enough to run project:
      
      ./manage.py runserver

Project sources are inside 'danceschool/competitions'.
Everything else is a part of original 'django-daanceschool' project and is needed to launch 'competitions'.
