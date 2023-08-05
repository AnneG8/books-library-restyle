from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from livereload import Server, shell
from more_itertools import chunked
import argparse
import json
import re
import os

 
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


def on_reload(books):
    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template('template.html')
    rendered_page = template.render(books=books)
    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def main():
    parser = create_parser()
    args = parser.parse_args()

    book_path = Path(args.dest_folder) / 'books' / ''       # может вызвать ошибку?
    images_path = Path(args.dest_folder) / 'images' / ''
    json_path = Path(args.json_path, 'book_list.json')
    try:
        check_path(book_path)
        check_path(images_path)
        check_path(json_path)
    except FileNotFoundError as err:
        path = err.args[0]
        print(f'Путь {path} не найден')
        return
    except PermissionError as err:
        path = err.args[0]
        print(f'Недостаточно прав доступа для чтения {path}')
        return

    with open(json_path, 'r', encoding='utf8') as file:
        books = json.load(file)
    books = list(chunked(books, 2))
    on_reload(books)

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')




if __name__ == '__main__':
    main()
