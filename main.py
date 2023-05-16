import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
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
    header_text = soup.find('td', class_='ow_px_td').find('h1').text
    filename = header_text.split('::')[0].strip()
    return filename


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    filepath = os.path.join(folder,  f'{sanitize_filename(filename)}.txt')
    with open(filepath, 'wb') as file:
        file.write(response.content)
        

def main():
    books_dir = 'books'
    Path(books_dir).mkdir(parents=True, exist_ok=True)

    for num in range(1, 11):
        try:
            filename = parse_book_info(get_page_url(num))
            download_txt(get_text_url(num), filename)
        except requests.HTTPError:
            continue
            


if __name__ == '__main__':
    main()

#    for num in range(1, 11):
#        response = requests.get(get_text_url(num))
#        response.raise_for_status()
#        try:
#            check_for_redirect(response)
#        except requests.HTTPError:
#            continue
#        else:
#            filename = f'{books_dir}\id{num}.txt'
#            with open(filename, 'wb') as file:
#                file.write(response.content)

