import os
import re
import tempfile
import requests
from flask import Flask, render_template_string, request, send_file, after_this_request
import yt_dlp

TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SoundCloud Downloader</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Righteous&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          fontFamily: { heading: ['Righteous', 'cursive'], body: ['Poppins', 'sans-serif'] },
          colors: { primary: '#1E1B4B', secondary: '#4338CA', cta: '#22C55E', dark: '#0F0F23', light: '#F8FAFC' },
        }
      }
    }
  </script>
</head>
<body class="font-body bg-dark text-light min-h-screen">
  <div class="flex flex-col min-h-screen">
    <header class="flex items-center justify-between px-6 py-5 max-w-6xl mx-auto w-full">
      <div class="flex items-center gap-3">
        <svg class="w-8 h-8 text-cta" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" />
        </svg>
        <span class="font-heading text-xl tracking-wide">SC<span class="text-cta">Dow</span></span>
      </div>
      <nav class="flex gap-6 text-sm text-gray-400">
        <a href="#" class="hover:text-light transition-colors duration-200 cursor-pointer">Главная</a>
        <a href="https://soundcloud.com" target="_blank" class="hover:text-light transition-colors duration-200 cursor-pointer">SoundCloud</a>
      </nav>
    </header>
    <main class="flex-1 flex flex-col items-center justify-center px-4 py-12">
      <div class="max-w-2xl w-full text-center">
        <h1 class="font-heading text-5xl md:text-7xl mb-4 leading-tight">SoundCloud<br><span class="text-cta">Downloader</span></h1>
        <p class="text-gray-400 text-lg mb-10 max-w-lg mx-auto">Скачивай треки в MP3 одним кликом. Вставь ссылку — получи файл.</p>
        <form method="POST" action="/download" id="downloadForm" class="space-y-4">
          <div class="flex flex-col sm:flex-row gap-3 max-w-xl mx-auto">
            <input type="text" name="url" placeholder="https://soundcloud.com/artist/track" required
              class="flex-1 px-5 py-4 rounded-xl bg-[#1a1a3e] border border-[#2a2a5e] text-light placeholder-gray-500 focus:outline-none focus:border-cta focus:ring-1 focus:ring-cta transition-all duration-200 text-sm">
            <button type="submit" id="submitBtn"
              class="px-8 py-4 rounded-xl bg-cta text-dark font-semibold hover:bg-emerald-400 transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 text-sm sm:text-base whitespace-nowrap">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
              </svg>
              Скачать
            </button>
          </div>
        </form>
        <div id="loading" class="hidden mt-10">
          <div class="flex flex-col items-center gap-4">
            <div class="w-12 h-12 border-4 border-[#2a2a5e] border-t-cta rounded-full animate-spin"></div>
            <p class="text-gray-400 text-sm">Скачиваю и конвертирую в MP3...</p>
          </div>
        </div>
        {% if error %}
        <div class="mt-8 p-4 rounded-xl bg-red-900/30 border border-red-500/40 text-red-300 text-sm max-w-xl mx-auto">{{ error }}</div>
        {% endif %}
      </div>
    </main>
    <footer class="text-center py-6 text-gray-600 text-xs border-t border-[#1a1a3e]">
      <p>Работает на yt-dlp + FFmpeg</p>
    </footer>
  </div>
  <script>
    document.getElementById('downloadForm').addEventListener('submit', function() {
      document.getElementById('submitBtn').disabled = true;
      document.getElementById('submitBtn').innerHTML = '<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Загрузка...';
      document.getElementById('loading').classList.remove('hidden');
    });
  </script>
</body>
</html>"""

app = Flask(__name__)

API_BASE = 'https://api-v2.soundcloud.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

def _get_client_id():
    resp = requests.get('https://soundcloud.com/', headers=HEADERS, timeout=15)
    page = resp.text
    for src in reversed(re.findall(r'<script[^>]+src="([^"]+)"', page)):
        if src.startswith('/'):
            src = 'https://soundcloud.com' + src
        elif src.startswith('//'):
            src = 'https:' + src
        try:
            js = requests.get(src, headers=HEADERS, timeout=10)
            cid = re.search(r'client_id\s*:\s*"([0-9a-zA-Z]{32})"', js.text)
            if cid:
                return cid.group(1)
        except Exception:
            continue
    return None

def _resolve_track_id(url, client_id):
    m = re.search(r'/tracks/(\d+)', url)
    if m:
        return m.group(1)
    m = re.search(r'soundcloud\.com/([\w-]+)/([\w-]+)', url)
    if not m:
        return None
    uploader, title = m.group(1), m.group(2)
    title_clean = re.sub(r'-\d+$', '', title).replace('-', ' ')
    params = {'q': title_clean, 'client_id': client_id, 'limit': 20, 'offset': 0}
    try:
        resp = requests.get(f'{API_BASE}/search/tracks', headers=HEADERS, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for track in data.get('collection', []):
            pu = track.get('permalink_url', '')
            permalink = track.get('permalink', '')
            if uploader.lower() in pu.lower() and title.lower() in pu.lower():
                return str(track['id'])
            if uploader.lower() in pu.lower() and title.lower() in permalink.lower():
                return str(track['id'])
        if data.get('collection'):
            return str(data['collection'][0]['id'])
    except Exception:
        return None
    return None

def download_track(url, output_dir):
    client_id = _get_client_id()
    if not client_id:
        raise Exception('Не удалось получить client_id')

    track_id = _resolve_track_id(url, client_id)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    try:
        from yt_dlp.cookies import SUPPORTED_BROWSERS
        for browser in ['firefox', 'chrome', 'chromium']:
            if browser in SUPPORTED_BROWSERS:
                ydl_opts['cookiesfrombrowser'] = (browser,)
                break
    except Exception:
        pass

    dl_url = f'https://api.soundcloud.com/tracks/{track_id}' if track_id else url
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(dl_url, download=True)
        title = info.get('title', 'track')
        return os.path.join(output_dir, f"{title}.mp3")

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    if not url:
        return render_template_string(TEMPLATE, error='Введите URL трека')

    tmp = tempfile.mkdtemp()
    try:
        filepath = download_track(url, tmp)
        @after_this_request
        def cleanup(response):
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
            return response
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        return render_template_string(TEMPLATE, error=f'Ошибка: {e}')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
