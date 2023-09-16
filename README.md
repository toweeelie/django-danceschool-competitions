# django-danceschool-competitions
Competitions app for django-danceschool project

Tested to work with WSL2 (Ubuntu 22.04) on Win11. Installation steps:

1. It's better to prepare virtual environment for python packages:
      
            python3 -m venv ./venv 
            source venv/bin/activate

2. Dependencies installation may take some time, maybe something here is not necessary, but most of installation time is Django installation, so removing unnecessary apps will not reduce installation time dramatically:
      
            pip install -r requirements.txt
  
3. Next step is to create new DB and superuser:
      
            ./manage.py migrate
            ./manage.py createsuperuser
  
This should be enough to run project:
      
      ./manage.py runserver

Starting page shows lists of available competitions. Competition can be added through admin panel: http://127.0.0.0.1:8000/admin/

Skating table calculator is also available at http://127.0.0.1:8000/skatingcalculator/
