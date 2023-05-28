from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import requests
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
    parser = argparse.ArgumentParser(
        description='Download sci-fi books from tululu.org, page by page.'
                    'One page contains about 25 books')
    parser.add_argument('-s', '--start_page', 
                        type=check_non_negative,
                        default=1, const=1,   
                        nargs='?',
                        help='first page number')
    parser.add_argument('-e', '--end_page', 
                        type=check_non_negative,
                        default=4, const=4,   
                        nargs='?',
                        help='last page number')
    parser.add_argument('-f', '--dest_folder', 
                        type=str,
                        default='', const='',   
                        nargs='?',
                        help='choose dest folder for books and images')
    parser.add_argument('-j', '--json_path', 
                        type=str,
                        default='', const='',   
                        nargs='?',
                        help='choose book_list.json')
    parser.add_argument('-skt', '--skip_txt', 
                        action='store_true',
                        help='allows to refuse download books')
    parser.add_argument('-ski', '--skip_imgs', 
                        action='store_true',
                        help='allows to refuse download images')
    return parser


def prepare_dirs(dest_folder):
    dirs = {
        'books': Path(dest_folder) / 'books' / '',
        'images': Path(dest_folder) / 'images' / ''
    }
    for file_dir in dirs:
        Path(file_dir).mkdir(parents=True, exist_ok=True)
    return dirs


def check_for_redirect(response):
    if(response.history):
        raise requests.HTTPError


def get_response(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response;


def parse_genre_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    base_page_url = 'https://tululu.org/'
    book_urls = [
        urljoin(base_page_url, book.select_one('a')['href'])
        for book in soup.select('.d_book')
    ]
    return book_urls


def parse_book_page(response):
    soup = BeautifulSoup(response.text, 'lxml')
    header = soup.select_one('.ow_px_td h1').text.split('::')
    genres = [genre.text for genre in soup.select('span.d_book a')]
    image = soup.select_one('.bookimage img')['src']
    comments = [texts.text for texts in soup.select('.texts .black')]
    return {
       'title': header[0].strip(),
       'author': header[1].strip(),
       'img_url': urljoin(response.url, image),
       'comments': comments,
       'genres': genres
    }


def download_txt(book_num, filename, folder):
    payload = {'id': book_num}
    response = requests.get('https://tululu.org/txt.php', params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    filepath = str(Path(
        folder, 
        f'{book_num}. {sanitize_filename(filename)}.txt'
    ))
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath


def is_file_valid(filepath):
    path = Path(filepath)
    return (path.exists() and path.is_file())


def download_image(url, folder):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    image_name = urlsplit(unquote(url)).path.split("/")[-1]
    image_path = str(Path(folder, image_name))
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


def get_book(url, args, dirs):
    book = parse_book_page(get_response(url))
    url_path = urlsplit(unquote(url)).path
    num = re.sub('[/b]', '', url_path)
    if not args.skip_txt:
        book['book_path'] = download_txt(num, book['title'], dirs['books'])
    if (is_file_valid(book['book_path']) 
        and not args.skip_imgs):
        book['img_scr'] = download_image(book['img_url'], dirs['images'])
        del book['img_url']
        return book
    return


def get_books_from_page(page_num, args, dirs):
    genre_page_url = 'https://tululu.org/l55/{}/'
    book_urls = parse_genre_page(
        get_response(genre_page_url.format(page_num))
    )
    page_books = list()
    for url in book_urls:
        while True:
            try:
                book = get_book(url, args, dirs)
                if book:
                    page_books.append(book)
                break
            except requests.HTTPError:
                break
            except requests.ConnectionError:
                time.sleep(3)
    return page_books


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        dirs = prepare_dirs(args.dest_folder)
    except PermissionError:
        print(f'Не хватает прав доступа для {args.dest_folder}')
        return

    books = list()
    for page_num in range(args.start_page, args.end_page + 1):
        while True:
            try:
                books.extend(get_books_from_page(page_num, args, dirs))
                break
            except requests.HTTPError:
                break
            except requests.ConnectionError:
                time.sleep(3)
    
    book_list_json = json.dumps(books, ensure_ascii=False, indent=2)
    json_name = Path(args.json_path, 'book_list.json')
    with open(json_name, 'w', encoding='utf8') as my_file:
        my_file.write(book_list_json)
            

if __name__ == '__main__':
    main()

