import os

def find_files_with_extensions(extensions, directory):
    matches = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                matches.append(os.path.join(root, file))
    return matches

video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']

current_directory = os.getcwd()

video_files = find_files_with_extensions(video_extensions, current_directory)

for video_file in video_files:
    print(video_file)

for video_file in video_files:
    try:
        os.remove(video_file)
        print(f"Удален: {video_file}")
    except Exception as e:
        print(f"Ошибка при удалении {video_file}: {e}")

print("Удаление видеофайлов завершено.")
