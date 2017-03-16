source /home/matt/virtualenvs/hook/bin/activate
coverage run setup.py test
coverage combine
coverage report -m
coverage html 
