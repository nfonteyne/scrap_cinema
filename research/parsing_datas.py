import requests
from bs4 import BeautifulSoup
import datetime

def scrape_cinema(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Add your parsing logic here
    return movies

def main():
    cinemas = [
        "https://www.allocine.fr/seance/salle_gen_csalle=C0050.html"
    ]
    
    all_movies = {}
    for cinema_url in cinemas:
        movies = scrape_cinema(cinema_url)
        all_movies[cinema_url] = movies

    # Save or process the scraped data
    
if __name__ == "__main__":
    main()
