from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import requests
import os
import argparse
import time


def check_positive(value):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError(
            "invalid positive int value: '%s'" % int_value
        )
    return int_value


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start_id', 
                        type=check_positive,
                        default=1, const=1,   
                        nargs='?')
    parser.add_argument('-e', '--end_id', 
                        type=check_positive,
                        default=10, const=10,   
                        nargs='?')
    return parser


def check_for_redirect(response):
    if(response.history):
        raise requests.HTTPError


def get_page_response(num):
    page_url = 'https://tululu.org/b{}/'
    response = requests.get(page_url.format(num))
    response.raise_for_status()
    check_for_redirect(response)
    return response;


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
       'genres': genres,
       'image': urljoin(response.url, image),
       'comments': comments,
    }
     

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


def download_image(url, folder='images/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    image_name = urlsplit(unquote(url)).path.split("/")[-1]
    image_path = os.path.join(folder, image_name)
    with open(image_path, 'wb') as file:
        file.write(response.content)


def main():
    books_dirs = ['books', 'images']
    for books_dir in books_dirs:
        Path(books_dir).mkdir(parents=True, exist_ok=True)

    parser = create_parser()
    args = parser.parse_args()

    missing_pages = list()
    for num in range(args.start_id, args.end_id + 1):
        while True:
            try:
                book = parse_book_page(get_page_response(num))
                download_txt(num, book['title'])
                download_image(book['image'])    
                break
            except requests.HTTPError:
                missing_pages.append(str(num))
                break
            except requests.ConnectionError:
                time.sleep(5)
    if missing_pages:
        print('Не были скачаны книги: ', ','.join(missing_pages))
            

if __name__ == '__main__':
    main()

