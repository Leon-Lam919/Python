import requests
from bs4 import BeautifulSoup

URL= requests.get('https://realpython.github.io/fake-jobs/')

text = URL.text
status = URL.status_code

soup = BeautifulSoup(URL.content, "html.parser")

results = soup.find(id="ResultsContainer")
print(results.prettify())