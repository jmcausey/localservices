#!/bin/bash

echo 'cd localservices'
cd localservices
echo 'pip install -r requirments'
pip install -r requirements.txt
echo 'flask --app flaskr init-db'
flask --app flaskr init-db
echo 'Successfully install localservices'
