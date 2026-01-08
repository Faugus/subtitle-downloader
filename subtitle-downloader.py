#!/usr/bin/env python3

import sys
import os
import re
import struct
import gzip
import shutil
import base64
import configparser
import xmlrpc.client

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


class SubtitleDownloader(QWidget):
    CONFIG_DIR = os.path.expanduser("~/.config/subtitle-downloader")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
    ICON_FILE = "/usr/share/icons/hicolor/256x256/apps/subtitle-downloader.png"

    LANGUAGES = {
        'eng': 'English',
        'cze': 'Czech',
        'dan': 'Danish',
        'dut': 'Nederlands',
        'fin': 'Finnish',
        'fre': 'Français',
        'ell': 'Greek',
        'baq': 'Basque',
        'pob': 'Brazilian Portuguese',
        'por': 'Portuguese (Portugal)',
        'rum': 'Romanian',
        'slo': 'Slovak',
        'spa': 'Spanish',
        'swe': 'Swedish',
        'ukr': 'Ukrainian',
        'hun': 'Hungarian',
        'scc': 'Serbian'
    }

    def __init__(self, video_path=None):
        super().__init__()

        self.setWindowTitle("Subtitle Downloader")
        self.setFixedSize(720, 360)
        if os.path.isfile(self.ICON_FILE):
            self.setWindowIcon(QIcon(self.ICON_FILE))

        self.server = xmlrpc.client.ServerProxy(
            "https://api.opensubtitles.org/xml-rpc"
        )
        self.token = None
        self.video_path = video_path

        self._load_config()
        self._build_ui()

    # ---------------- CONFIG ----------------

    def _load_config(self):
        self.config = configparser.ConfigParser()
        os.makedirs(self.CONFIG_DIR, exist_ok=True)

        if os.path.isfile(self.CONFIG_FILE):
            self.config.read(self.CONFIG_FILE)
        else:
            self.config['settings'] = {'language': 'pob'}
            with open(self.CONFIG_FILE, 'w') as f:
                self.config.write(f)

    def _save_language(self, code):
        self.config['settings']['language'] = code
        with open(self.CONFIG_FILE, 'w') as f:
            self.config.write(f)

    # ---------------- UI ----------------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.file_button = QPushButton("Choose a video")
        self.file_button.clicked.connect(self.choose_video)
        layout.addWidget(self.file_button)

        if self.video_path and os.path.isfile(self.video_path):
            self._update_file_button()

        self.lang_combo = QComboBox()
        for code, name in self.LANGUAGES.items():
            self.lang_combo.addItem(name, code)

        default_lang = self.config.get('settings', 'language', fallback='pob')
        idx = self.lang_combo.findData(default_lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        layout.addWidget(self.lang_combo)

        self.search_button = QPushButton("Search Subtitles")
        self.search_button.clicked.connect(self.on_search)
        layout.addWidget(self.search_button)

        # ---------- CAMPO DE FILTRO (INICIALMENTE OCULTO) ----------
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter subtitles...")
        self.filter_edit.textChanged.connect(self.filter_subtitles)
        self.filter_edit.hide()
        layout.addWidget(self.filter_edit)

        self.subtitle_list = QListWidget()
        self.subtitle_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.subtitle_list, 1)

        self.download_button = QPushButton("Download Selected")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.on_download)
        layout.addWidget(self.download_button)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    # ---------------- HELPERS ----------------

    def _update_file_button(self):
        filename = os.path.basename(self.video_path)
        self.file_button.setText(filename)
        self.file_button.setToolTip(self.video_path)

    def choose_video(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Choose video",
            "",
            "Videos (*.mkv *.mp4 *.avi *.mov *.wmv)"
        )
        if file:
            self.video_path = file
            self._update_file_button()

    def on_language_changed(self):
        code = self.lang_combo.currentData()
        if code:
            self._save_language(code)

    def login(self):
        if self.token:
            return True

        resp = self.server.LogIn('', '', 'en', 'VLSub 0.10')
        self.token = resp.get('token')

        return bool(self.token)

    def compute_hash(self, path):
        buf_size = 65536
        size = os.path.getsize(path)
        hash_value = size

        if size < buf_size * 2:
            return None, size

        with open(path, 'rb') as f:
            start = f.read(buf_size)
            f.seek(size - buf_size)
            end = f.read(buf_size)

        data = start + end
        for i in range(0, len(data), 8):
            block = data[i:i + 8]
            if len(block) < 8:
                break
            value = struct.unpack('<Q', block)[0]
            hash_value = (hash_value + value) & 0xFFFFFFFFFFFFFFFF

        return f"{hash_value:016x}", size

    # ---------------- FILTER ----------------

    def filter_subtitles(self, text):
        text = text.lower().strip()

        for i in range(self.subtitle_list.count()):
            item = self.subtitle_list.item(i)
            item.setHidden(text not in item.text().lower())

    # ---------------- SEARCH ----------------

    def on_search(self):
        if not self.video_path:
            self.status_label.setText("Select a video.")
            return

        self.login()
        if not self.token:
            self.status_label.setText("Login failed.")
            return
        self.subtitle_list.clear()
        self.filter_edit.clear()
        self.filter_edit.hide()

        filename = os.path.basename(self.video_path)
        name, _ = os.path.splitext(filename)

        pattern = re.compile(
            r'(?i)(?P<series>.+?)[._\- ]+(?P<episode>s\d{2}e\d{2})'
        )
        match = pattern.search(name)

        if match:
            series = re.sub(r'[._\-]+', ' ', match.group('series'))
            episode = match.group('episode').lower()
            query = f"{series} {episode}"
        else:
            query = re.sub(r'[._\-]+', ' ', name)

        query = ' '.join(query.split())
        lang = self.lang_combo.currentData()

        self.status_label.setText("Searching...")

        moviehash, size = self.compute_hash(self.video_path)
        params = []

        if moviehash:
            params.append({
                'moviehash': moviehash,
                'moviebytesize': str(size),
                'sublanguageid': lang
            })

        params.append({
            'query': query,
            'sublanguageid': lang
        })

        resp = self.server.SearchSubtitles(self.token, params)
        subs = resp.get('data') or []

        if not subs:
            self.status_label.setText("No subtitles found.")
            return

        for s in subs:
            item = QListWidgetItem(s['SubFileName'])
            item.setData(Qt.ItemDataRole.UserRole, s['IDSubtitleFile'])
            self.subtitle_list.addItem(item)

        if self.subtitle_list.count() > 0:
            self.filter_edit.show()

        self.status_label.setText(f"{len(subs)} subtitle(s) found.")

    # ---------------- DOWNLOAD ----------------

    def on_selection_changed(self):
        self.download_button.setEnabled(
            len(self.subtitle_list.selectedItems()) > 0
        )

    def on_download(self):
        items = self.subtitle_list.selectedItems()
        if not items:
            return

        sub_id = items[0].data(Qt.ItemDataRole.UserRole)

        out_dir = os.path.dirname(self.video_path)
        out_name = os.path.splitext(
            os.path.basename(self.video_path)
        )[0] + '.srt'
        out_path = os.path.join(out_dir, out_name)

        data = self.server.DownloadSubtitles(
            self.token, [sub_id]
        ).get('data')

        if not data:
            self.status_label.setText("Error downloading subtitle.")
            return

        blob = base64.b64decode(data[0]['data'])
        gz_path = out_path + '.gz'

        with open(gz_path, 'wb') as f:
            f.write(blob)

        with gzip.open(gz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

        os.remove(gz_path)
        self.status_label.setText("Subtitle downloaded!")


# ---------------- MAIN ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)

    video = sys.argv[1] if len(sys.argv) > 1 else None
    win = SubtitleDownloader(video)
    win.show()

    sys.exit(app.exec())
