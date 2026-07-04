
# 🎵 SCDow — SoundCloud Downloader

Простой и быстрый веб-интерфейс для скачивания треков с SoundCloud в формате MP3 (192 kbps) в один клик. Разработано на Flask и yt-dlp.

## 🚀 Особенности
* **Скачивание в один клик:** Просто вставь ссылку на трек и нажми кнопку.
* **Автоматическая конвертация:** Сервер сам конвертирует аудио в MP3 через FFmpeg.
* **Минималистичный дизайн:** Интерфейс написан на Tailwind CSS с приятной темной темой и плавной анимацией загрузки.
* **Динамический порт:** Готов к быстрому деплою на популярные хостинги.

## 🛠️ Технологии
* **Backend:** Python 3, Flask
* **Core:** yt-dlp
* **Media Processing:** FFmpeg
* **Frontend:** Tailwind CSS, HTML5, JavaScript

## 📦 Локальный запуск

### Требования
В системе должен быть установлен **FFmpeg**. 
* На Linux (Arch): `sudo pacman -S ffmpeg`
* На Linux (Debian/Ubuntu): `sudo apt install ffmpeg`

### Установка & запуск
1. Клонируй репозиторий:
   ```bash
   git clone [https://github.com/Anmuzzz/scdow.git](https://github.com/Anmuzzz/scdow.git)
   cd scdow

```

2. Установи зависимости:
```bash
pip install -r requirements.txt

```


3. Запусти приложение:
```bash
python app.py

```


После этого открой в браузере `http://localhost:5000`.

## 🌐 Деплой (Deployment)

Проект полностью готов для деплоя на **Render**, **Fly.io** или **Sprinthost**. При развертывании в облаке убедись, что в среде окружения (через Buildpack или Docker) добавлен компонент **FFmpeg**, иначе конвертация скачанных аудиодорожек в формат MP3 выдаст ошибку.

```
