#!/bin/bash
for app in tests
do
  python manage.py dumpdata $app --indent 2 > $app/fixtures/$app.json 
done
