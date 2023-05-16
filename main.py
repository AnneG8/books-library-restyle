import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import os


def get_text_url(num):
    return f'https://tululu.org/txt.php?id={num}'


def get_page_url(num):
    return f'https://tululu.org/b{num}/'   


def check_for_redirect(response):
    if(response.history and response.history[-1].is_redirect):
        raise requests.HTTPError


def parse_book_info(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    soup = BeautifulSoup(response.text, 'lxml')
    header = soup.find('td', class_='ow_px_td').find('h1').text.split('::')
    image = soup.find('div', class_='bookimage').find('img')['src']
    comments = list()
    for texts in soup.find_all('div', class_='texts'):
        comments.append(texts.find('span').text) 
    return {
       'title': header[0].strip(),
       'author': header[1].strip(),
       'image': urljoin(url, image),
       'comments': comments,
    }


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    filepath = os.path.join(folder, f'{sanitize_filename(filename)}.txt')
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

    for num in range(1, 11):
        try:
            book = parse_book_info(get_page_url(num))
            download_txt(get_text_url(num), book.title)
            download_image(book['image'])
        except requests.HTTPError:
            continue
            

if __name__ == '__main__':
    main()

