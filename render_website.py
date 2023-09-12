from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from livereload import Server, shell
from more_itertools import chunked
import argparse
import json
import os


BOOKS_ON_PAGE = 20
PAGES_FOLDER = 'pages\\'

 
def create_parser():
    parser = argparse.ArgumentParser(
        description='Download sci-fi books from tululu.org, page by page.'
                    'One page contains about 25 books')
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
    return parser


def check_path(path):
    if not os.access(path, os.F_OK):
        raise FileNotFoundError(path)
    if not os.access(path, os.R_OK):
        raise PermissionError(path)
    return


def on_reload(json_path, dest_folder, folder=PAGES_FOLDER):
    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template('template.html')

    with open(json_path, 'r', encoding='utf8') as file:
        books = json.load(file)
    for book in books:
        book['book_path'] = str(Path(dest_folder, book['book_path']))
        if book.get('img_scr'):
            book['img_scr'] = str(Path(dest_folder, book['img_scr']))

    books = list(chunked(books, BOOKS_ON_PAGE))
    for num, book_set in enumerate(books, 1):
        columns_num = 2
        book_set = list(chunked(book_set, columns_num))
        rendered_page = template.render(
            book_set=book_set,
            page_number=num,
            pages_count=len(books)
        )

        filename = Path(folder, f'index{num}.html')
        with open(filename, 'w', encoding="utf8") as file:
            file.write(rendered_page)


def add_path(func, json_path, dest_folder):
    def _wrapper():
        func(json_path, dest_folder)
    return _wrapper


def main():
    parser = create_parser()
    args = parser.parse_args()

    dest_folder = args.dest_folder
    json_path = Path(args.json_path, 'book_list.json')
    try:
        check_path(Path(dest_folder) / 'media' / 'books' / '')
        check_path(Path(dest_folder) / 'media' / 'images' / '')
        check_path(json_path)
    except FileNotFoundError as err:
        path = err.args[0]
        print(f'Путь {path} не найден')
        return
    except PermissionError as err:
        path = err.args[0]
        print(f'Недостаточно прав доступа для чтения {path}')
        return

    Path(PAGES_FOLDER).mkdir(parents=True, exist_ok=True)

    on_reload(json_path, dest_folder)

    server = Server()
    server.watch('template.html', 
                 add_path(on_reload, json_path, dest_folder))
    server.serve(root='.')


if __name__ == '__main__':
    main()
