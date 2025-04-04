import requests
from bs4 import BeautifulSoup
import os,re,time
# URL CNN
url = "https://www.cnn.com/world"

response = requests.get(url)
if response.status_code != 200:
    print("Unable to access the website!")
    exit()

#Analyse HTML by BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

article_links = soup.find_all("a", class_="container__link")

# save article links in cnn
full_links = []
base_url = "https://www.cnn.com"
for link in article_links:
    href = link.get("href")  
    if href:
        if href.startswith("/"):
            full_link = base_url + href
        else:
            full_link = href
        full_links.append(full_link)

for i, link in enumerate(full_links, 1):
    print(f"{i}. {link}")


with open("cnn_article_links.txt", "w") as file:
    for link in full_links:
        file.write(link + "\n")


# read file txt and get link list
with open("cnn_article_links.txt", "r") as file:
    links = file.readlines()

links = [link.strip() for link in links]
os.makedirs('cnn_articles')
for i,link in enumerate(links):
    main_category_url = link


    response = requests.get(main_category_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        a_tags = soup.find_all(class_="article__content")

        if a_tags:
            # Replace invalid characters
            filename = link.split('/')[-2] + ".txt"
            
            with open(os.path.join('cnn_articles', filename), "w", encoding="utf-8") as file:
                # Write the content of the a_tags to the file
                for tag in a_tags:
                    file.write(tag.get_text() + "\n")
            
             # Increment the count after saving an article
            print(f"Saved article {i+1} into {filename}")

    else:
        print(f"Unable to access the article {i+1}: {link}")

    time.sleep(2)  
