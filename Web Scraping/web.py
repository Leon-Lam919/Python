import requests

r= requests.get('https://codedamn-classrooms.github.io/webscraper-python-codedamn-classroom-website/')

text = r.text
status = r.status_code

print(text, status)

