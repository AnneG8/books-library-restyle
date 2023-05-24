from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import requests
import os
import argparse
import re
import time
import json


def check_non_negative(value):
    int_value = int(value)
    if int_value < 0:
        raise argparse.ArgumentTypeError(
            "invalid positive int value: '%s'" % int_value
        )
    return int_value


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_page', 
                        type=check_non_negative,
                        default=1, const=1,   
                        nargs='?')
    parser.add_argument('-e', '--end_page', 
                        type=check_non_negative,
                        default=4, const=4,   
                        nargs='?')
    return parser


def get_response(url):
    response = requests.get(url)
    response.raise_for_status()
    return response;


def parse_genre_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    base_page_url = 'https://tululu.org/'
    book_urls = [
        urljoin(base_page_url, book.find('tr').find('a')['href'])
        for book in soup.find('td', class_='ow_px_td').find_all('table')
    ]
    return book_urls


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    header = soup.find('td', class_='ow_px_td').find('h1').text.split('::')
    genres = [genre.text 
              for genre 
              in soup.find('span', class_='d_book').find_all('a')]
    image = soup.find('div', class_='bookimage').find('img')['src']
    comments = [texts.find('span').text 
                for texts 
                in soup.find_all('div', class_='texts')]
    return {
       'title': header[0].strip(),
       'author': header[1].strip(),
       'img_url': urljoin(response.url, image),
       'comments': comments,
       'genres': genres
    }
     

def check_for_redirect(response):
    if(response.history):
        raise requests.HTTPError


def download_txt(book_num, filename, folder='books/'):
    payload = {'id': book_num}
    response = requests.get('https://tululu.org/txt.php', params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    filepath = os.path.join(
        folder, 
        f'{book_num}. {sanitize_filename(filename)}.txt'
    )
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def is_file_valid(filepath):
    path = Path(filepath)
    return (path.exists() and path.is_file())


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    image_name = urlsplit(unquote(url)).path.split("/")[-1]
    image_path = os.path.join(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


def main():
    books_dirs = ['books', 'images']
    for books_dir in books_dirs:
        Path(books_dir).mkdir(parents=True, exist_ok=True)

    parser = create_parser()
    args = parser.parse_args()

    genre_page_url = 'https://tululu.org/l55/{}/'
    books = list()
    for page_num in range(args.start_page, args.end_page + 1):
        book_urls = parse_genre_page(
            get_response(genre_page_url.format(page_num))
        )
        for url in book_urls:
            while True:
                try:
                    book = parse_book_page(get_response(url))
                    url_path = urlsplit(unquote(url)).path
                    num = re.sub('[/b]', '', url_path)
                    book['book_path'] = download_txt(num, book['title'])
                    if(is_file_valid(book['book_path'])):
                        book['img_scr'] = download_image(book['img_url'])
                        books.append(book)
                    break
                except requests.HTTPError:
                    break
                except requests.ConnectionError:
                    time.sleep(5)
    
    book_list_json = json.dumps(books, ensure_ascii=False, indent=2)
    with open("book_list.json", "w", encoding='utf8') as my_file:
        my_file.write(book_list_json)
            

if __name__ == '__main__':
    main()

