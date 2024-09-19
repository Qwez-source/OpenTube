# OpenTube
Альтернативный клиент ютуба в консоли без `youtube api`.

_______________________

# Установка
Все очень просто, нужно лишь установить необходимые библиотеки:
```python
pip install playwright requests pillow rich beautifulsoup4
```
Также не забудьте дополнительные файлы для `playwright`:
```python
playwright install
```
________________________

# Дополнительно

## Как это работает

Интерфейс реализован через библиотеку `rich`, то-есть, интерфейс моего клиента полностью консольный.
Поиск видео сделан через обычный парсинг `invidious` через `beautifulsoup4`.
Скачивание видео реализовано через запуск сайта через `playwright` в `headless` режиме (невидимый браузер).

## Удаление лишних видео
`OpenTube` не удаляет видео-файлы автоматически, если вам лень удалять все вручную я написал для этого [небольшой скрипт](https://github.com/Qwez-source/OpenTube/blob/main/clear_videos.py)
