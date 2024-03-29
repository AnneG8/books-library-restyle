from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin, urlsplit, unquote
import requests
import argparse
import re
import time
import json
import logging


class EmptyBookError(TypeError):
    pass


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


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


def get_response(url):
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response


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
    filename = f'{book_num}. {sanitize_filename(filename)}.txt'
    filepath = str(Path(folder, filename))
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


def get_book(url, skip_txt, skip_imgs, book_path, images_path):
    book = parse_book_page(get_response(url))
    url_path = urlsplit(unquote(url)).path
    num = re.sub('[/b]', '', url_path)
    if not skip_txt:
        book['book_path'] = download_txt(num, book['title'], book_path)
    if is_file_valid(book['book_path']) and not skip_imgs:
        book['img_scr'] = download_image(book['img_url'], images_path)
        del book['img_url']
        return book
    raise EmptyBookError


def get_books_from_page(page_num, skip_txt, skip_imgs,
                        book_path, images_path):
    genre_page_url = 'https://tululu.org/l55/{}/'
    book_urls = parse_genre_page(
        get_response(genre_page_url.format(page_num))
    )
    page_books = list()
    missing_pages = list()
    for url in book_urls:
        while True:
            try:
                book = get_book(url,
                                skip_txt, skip_imgs,
                                book_path, images_path)
                page_books.append(book)
                break
            except EmptyBookError:
                missing_pages.append(urlsplit(url).query)
                break
            except requests.HTTPError:
                logging.info('Не найдена страница книги '
                             f'{urlsplit(url).query}.')
                break
            except requests.ConnectionError:
                print('Не удается установить связь с tululu.org')
                time.sleep(3)
    return page_books, missing_pages


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        book_path = Path(args.dest_folder) / 'media' / 'books' / ''
        images_path = Path(args.dest_folder) / 'media' / 'images' / ''
        Path(book_path).mkdir(parents=True, exist_ok=True)
        Path(images_path).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f'Не хватает прав доступа для {args.dest_folder}')
        return

    try:
        json_path = Path(args.json_path, 'book_list.json')
        Path(args.json_path).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f'Не хватает прав доступа для {args.json_path}')
        return

    books = list()
    missing_book_pages = list()
    for page_num in range(args.start_page, args.end_page + 1):
        while True:
            try:
                page_books, missing_pages = get_books_from_page(
                    page_num, args.skip_txt, args.skip_imgs,
                    book_path, images_path)
                books.extend(page_books)
                missing_book_pages.extend(missing_pages)
                break
            except requests.HTTPError:
                logging.info(f'Не найдена {page_num} страница жанра.')
                break
            except requests.ConnectionError:
                print('Не удается установить связь с tululu.org')
                time.sleep(3)

    with open(json_path, 'w', encoding='utf8') as file:
        json.dump(books, file, ensure_ascii=False, indent=2)

    if missing_book_pages:
        print('Не были скачаны книги: ', ','.join(missing_book_pages))


if __name__ == '__main__':
    main()
