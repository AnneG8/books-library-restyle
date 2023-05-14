import requests
from pathlib import Path


def get_url(num):
    return f'https://tululu.org/txt.php?id={num}'


def main():
    books_dir = 'books'
    Path(books_dir).mkdir(parents=True, exist_ok=True)

    for num in range(1, 11):
        response = requests.get(get_url(num))
        response.raise_for_status() 
        filename = f'{books_dir}\id{num}.txt'
        with open(filename, 'wb') as file:
            file.write(response.content)


if __name__ == '__main__':
    main()