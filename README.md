# Парсер книг с сайта tululu.org

Программа скачивает книги с сайта [tululu.org](https://tululu.org/). 
Создает 2 папки `books` и `images`, в первой сохраняет сами книги в txt-формате, во второй - обложки этих книг.
Возможно указать диапазон скачиваемых книг.

### Как установить

Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```

### Аргументы

По-умолчанию программа скачивает 10 книг с id от 1 до 10. При необходимости можно задать свой диапазон, используя необязательные аргументы `--start_id` и `--end_id` (или их сокращения `-s` и `-e`, соответственно). 

**Важно!** Оба аргумента должны быть положительными целыми числами. `--end_id` должно быть не меньше `--start_id`.

### Запуск

Запустите программу командой

```bash
$ python main.py -s START -e END
```

, где вместо `START` и `END` первое и последнее id запрашиваемых книг.

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).