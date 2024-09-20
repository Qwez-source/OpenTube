from playwright.sync_api import sync_playwright
import requests
import os
import uuid
import subprocess
import threading
import time
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.table import Table
from rich import box
from rich.prompt import Prompt
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

console = Console()

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

clear_console()

def display_ascii_art():
    ascii_art = r"""
   ____  _____  ______ _   _   _______ _    _ ____  ______ 
  / __ \|  __ \|  ____| \ | | |__   __| |  | |  _ \|  ____|
 | |  | | |__) | |__  |  \| |    | |  | |  | | |_) | |__   
 | |  | |  ___/|  __| | . ` |    | |  | |  | |  _ <|  __|  
 | |__| | |    | |____| |\  |    | |  | |__| | |_) | |____ 
  \____/|_|    |______|_| \_|    |_|   \____/|____/|______|
                                                           
    """
    console.print(ascii_art, style="bold magenta")

def convert_invidious_to_youtube(invidious_url):
    if "invidious" in invidious_url:
        video_id = invidious_url.split('=')[-1]
        youtube_url = f"https://youtube.com/watch?v={video_id}"
        return youtube_url
    return invidious_url

def automate_download(youtube_url):
    clear_console()

    def reset_progress_tracker():
        return {
            'last_percentage': None,
            'unchanged_count': 0
        }
    
    def check_progress(progress_tracker, current_percentage):
        if current_percentage == progress_tracker['last_percentage']:
            progress_tracker['unchanged_count'] += 1
        else:
            progress_tracker['last_percentage'] = current_percentage
            progress_tracker['unchanged_count'] = 0
        
        return progress_tracker['unchanged_count'] >= 10

    retry_attempts = 0
    max_retries = 5
    download_attempted = False

    while retry_attempts <= max_retries and not download_attempted:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("https://ddownr.com/rusR/youtube-video-downloader")
                page.fill('input.input-url.link', youtube_url)
                page.click('button#load')

                download_link = None
                video_started_playing = False
                file_path = None

                console.print("[yellow]Ожидание загрузки на сервер...[/yellow]")

                progress_tracker = reset_progress_tracker()

                while not download_link:
                    try:
                        page.wait_for_selector('div.progress.animate-pulse', timeout=10000)
                        progress_width = page.evaluate(
                            'document.querySelector("div.progress.animate-pulse") ? document.querySelector("div.progress.animate-pulse").style.width : ""'
                        )

 
                        if progress_width == "100%":
                            download_link = page.evaluate(
                                'document.querySelector("a.btn-download") ? document.querySelector("a.btn-download").href : ""'
                            )
                            
                            if download_link:
                                clear_console()
                                console.print(f"[bold cyan]Видео успешно загрузилось на сервер[/bold cyan]")
                                file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), generate_unique_filename())
                                download_thread = threading.Thread(target=download_file, args=(download_link, file_path))
                                download_thread.start()

                                page.wait_for_timeout(2000)

                                if not video_started_playing and file_path:
                                    wait_for_file_size(file_path, 1 * 1024 * 1024)
                                    play_video(file_path)
                                    video_started_playing = True

                                download_thread.join()
                                
                                download_attempted = True
                                
                            else:
                                console.print("[bold red]Ошибка загрузки на сервер![/bold red]")
                            break

                        else:
                            progress_percentage = float(progress_width.replace('%', ''))
                            clear_console()
                            console.print(f"[green]Прогресс загрузки на сервер: {progress_percentage}%[/green]")

                            if check_progress(progress_tracker, progress_percentage):
                                console.print("[bold red]Прогресс загрузки не изменяется, повторная попытка...[/bold red]")
                                retry_attempts += 1
                                if retry_attempts > max_retries:
                                    console.print("[bold red]Максимальное количество попыток достигнуто, прерывание...[/bold red]")
                                    break

                                browser.close()
                                page = browser.new_page()
                                page.goto("https://ddownr.com/rusR/youtube-video-downloader")
                                page.fill('input.input-url.link', youtube_url)
                                page.click('button#load')
                                progress_tracker = reset_progress_tracker()
                                continue

                            if not video_started_playing and file_path and os.path.exists(file_path):
                                if os.path.getsize(file_path) > 1 * 1024 * 1024:
                                    play_video(file_path)
                                    video_started_playing = True
                            
                            page.wait_for_timeout(1000)

                    except Exception as e:
                        console.print(f"[bold red]Ошибка при получении прогресса: {e}[/bold red]")
                        retry_attempts += 1
                        if retry_attempts > max_retries:
                            console.print("[bold red]Максимальное количество попыток достигнуто, прерывание...[/bold red]")
                            break
                        console.print("[bold yellow]Повторная попытка...[/bold yellow]")

                        browser.close()
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.goto("https://ddownr.com/rusR/youtube-video-downloader")
                        page.fill('input.input-url.link', youtube_url)
                        page.click('button#load')
                        progress_tracker = reset_progress_tracker()
                        continue

                browser.close()

        except Exception as e:
            console.print(f"[bold red]Ошибка при запуске браузера: {e}[/bold red]")
            retry_attempts += 1
            if retry_attempts > max_retries:
                console.print("[bold red]Максимальное количество попыток достигнуто, прерывание...[/bold red]")
                break
            console.print("[bold yellow]Повторная попытка...[/bold yellow]")

def generate_unique_filename():
    return f"download_{uuid.uuid4().hex}.mp4"

def download_file(url, file_path):
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        with open(file_path, 'wb') as file:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                download_task = progress.add_task("[green]Загружается на ПК:[/green]", total=total_size)

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        progress.update(download_task, advance=len(chunk))
        clear_console()
        console.print(f"[bold green]Файл успешно загружен:[/bold green] {file_path}")
    except requests.RequestException as e:
        console.print(f"[bold red]Ошибка при загрузке файла: {e}[/bold red]")

def wait_for_file_size(file_path, min_size):
    last_size = 0
    unchanged_count = 0
    max_unchanged_attempts = 10

    while unchanged_count < max_unchanged_attempts:
        current_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        if current_size > last_size:
            last_size = current_size
            unchanged_count = 0
        else:
            unchanged_count += 1

        if current_size >= min_size:
            return True

        time.sleep(1)

    return False

def play_video(file_path):
    try:
        if os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', file_path))
        console.print(f"[bold blue]Видео успешно открыто: {file_path}[/bold blue]")
    except Exception as e:
        console.print(f"[bold red]Ошибка при открытии видео: {e}[/bold red]")

def display_thumbnail(thumbnail_url):
    try:
        response = requests.get(thumbnail_url)
        image = Image.open(BytesIO(response.content))
        image.show()
    except Exception as e:
        console.print(f"[bold red]Ошибка при загрузке и отображении обложки: {e}[/bold red]")

def search_videos_invidious(query):
    url = f"https://invidious.adminforge.de/search?q={query}"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    video_elements = soup.select('div.pure-u-1.pure-u-md-1-4')
    videos = []
    
    for element in video_elements:
        title_element = element.select_one('div.video-card-row > a > p')
        length_element = element.select_one('div.bottom-right-overlay > p.length')
        channel_element = element.select_one('div.video-card-row.flexible > div.flex-left > a > p.channel-name')
        views_element = element.select_one('div.video-card-row.flexible > div.flex-right > p.video-data:nth-of-type(1)')
        published_element = element.select_one('div.video-card-row.flexible > div.flex-left > p.video-data')
        link_element = element.select_one('div.thumbnail > a')
        thumbnail_element = element.select_one('div.thumbnail > a > img')

        title = title_element.text if title_element else "Н/Д"
        length = length_element.text if length_element else "Н/Д"
        channel = channel_element.text if channel_element else "Н/Д"
        views = views_element.text if views_element else "Н/Д"
        published = published_element.text if published_element else "Н/Д"
        thumbnail_url = f"https://invidious.adminforge.de{thumbnail_element['src']}" if thumbnail_element else "Н/Д"
        video_link = f"https://invidious.adminforge.de{link_element['href']}" if link_element else "Н/Д"

        if "Н/Д" in [title, channel, views, published, thumbnail_url, video_link]:
            continue

        video_info = {
            'Заголовок': title,
            'Длина': length,
            'Канал': channel,
            'Просмотры': views,
            'Опубликовано': published,
            'Миниатюра': thumbnail_url,
            'Ссылка': video_link
        }
        videos.append(video_info)
    
    return videos

def display_videos(videos, page_number=1, per_page=5):
    console = Console()
    total_pages = (len(videos) + per_page - 1) // per_page
    start_idx = (page_number - 1) * per_page
    end_idx = start_idx + per_page
    videos_on_page = videos[start_idx:end_idx]

    clear_console()
    
    table = Table(title=f"Видео (Страница {page_number} из {total_pages})", box=box.ROUNDED, title_style="bold magenta")
    table.add_column("№", justify="center", style="cyan", no_wrap=True)
    table.add_column("Заголовок", justify="left", style="green")
    table.add_column("Длина", justify="right", style="cyan")
    table.add_column("Канал", justify="left", style="yellow")
    table.add_column("Просмотры", justify="right", style="white")
    table.add_column("Опубликовано", justify="left", style="blue")

    for i, video in enumerate(videos_on_page, start=start_idx + 1):
        table.add_row(
            str(i),
            video['Заголовок'],
            video['Длина'],
            video['Канал'],
            video['Просмотры'],
            video['Опубликовано']
        )

    console.print(table)

    action = Prompt.ask("[bold blue] [bold green]'d[номер]'[/bold green] для загрузки, [bold green]'v[номер]'[/bold green] для просмотра обложки, [bold green]'n/p'[/bold green] для навигации по страницам или [bold green]'q'[bold green] для выхода")

    if action == "n" and page_number < total_pages:
        display_videos(videos, page_number + 1)
    if action == "q":
        exit()
    elif action == "p" and page_number > 1:
        display_videos(videos, page_number - 1)
    elif action == "n" or action == "p":
        display_videos(videos, page_number)
    elif action.startswith("d"):
        try:
            video_index = int(action[1:]) - 1
            if 0 <= video_index < len(videos):
                selected_video = videos[video_index]
                invidious_url = selected_video['Ссылка']
                youtube_url = convert_invidious_to_youtube(invidious_url)
                automate_download(youtube_url)
            else:
                console.print("[bold red]Неверный номер видео![/bold red]")
        except ValueError:
            console.print("[bold red]Неверный ввод! Пожалуйста, введите корректный номер.[/bold red]")
    elif action.startswith("v"):
        try:
            video_index = int(action[1:]) - 1
            if 0 <= video_index < len(videos):
                thumbnail_url = videos[video_index]['Миниатюра']
                display_thumbnail(thumbnail_url)

                display_videos(videos, page_number)
            else:
                console.print("[bold red]Неверный номер видео![/bold red]")
        except ValueError:
            console.print("[bold red]Неверный ввод! Пожалуйста, введите корректный номер.[/bold red]")

def main():
    display_ascii_art()

    while True:
        search_query = Prompt.ask("[bold blue]Введите запрос для поиска видео или [bold green]'q'[/bold green] для выхода[/bold blue]")

        if search_query.lower() == 'q':
            break
        
        clear_console()
        console.print(f"[bold green]Идет загрузка видео...")
        videos = search_videos_invidious(search_query)
        if videos:
            display_videos(videos)
        else:
            console.print("[bold red]Видео не найдены![/bold red]")

if __name__ == "__main__":
    main()
