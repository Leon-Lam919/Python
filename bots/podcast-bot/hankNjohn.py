from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

url = "https://www.imdb.com/title/tt16845574/episodes/?season=Unknown&ref_=ttep_ep_sn_nx"

# Selenium setup
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)  # Make sure chromedriver is in PATH
driver.get(url)

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

# Each episode container
episodes = soup.select("div.sc-5372d523-5.jBUStp")

data = []
for ep in episodes:
    # Get title
    title_div = ep.select_one("div.ipc-title__text.ipc-title__text--reduced")
    title = title_div.get_text(strip=True) if title_div else None

    # Get air date
    date_span = ep.select_one("span.sc-5372d523-10.knzESm")
    date_text = date_span.get_text(strip=True) if date_span else None

    # Convert to datetime
    date_obj = None
    if date_text:
        try:
            date_obj = datetime.strptime(date_text, "%a, %b %d, %Y")  # e.g., "Mon, Jun 8, 2015"
        except ValueError:
            try:
                date_obj = datetime.strptime(date_text, "%a, %B %d, %Y")
            except:
                pass

    data.append({"title": title, "airdate_text": date_text, "airdate": date_obj})

# Create DataFrame
df = pd.DataFrame(data)

# Filter November episodes
november_df = df[df["airdate"].notna() & (df["airdate"].dt.month == 11)]

print(november_df[["title", "airdate_text", "airdate"]])

# Optional: save to CSV
# november_df.to_csv("november_episodes.csv", index=False)
