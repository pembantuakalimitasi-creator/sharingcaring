# Mancave Vault - Aplikasi Web Python & SQLite

Aplikasi manajemen inventaris barang koleksi *mancave* premium yang menggunakan **Python** sebagai backend web server dan **SQLite** sebagai database lokal untuk menyimpan data barang secara permanen.

## Struktur File
* `app.py`: Backend web server menggunakan pustaka bawaan Python (`http.server` & `sqlite3`).
* `index.html`: Frontend visualisasi bertema cyberpunk-glassmorphism interaktif (HTML, CSS, JS).
* `mancave.db`: Database SQLite lokal (otomatis dibuat saat server pertama kali dijalankan).

---

## Cara Menjalankan Aplikasi di Windows

Karena Python belum terdeteksi di sistem PATH Windows Anda, ikuti langkah-langkah mudah berikut untuk menginstal dan menjalankannya:

### 1. Instalasi Python
1. Buka tautan resmi berikut untuk mengunduh installer Python terbaru untuk Windows: [Download Python](https://www.python.org/downloads/)
2. Jalankan file installer yang telah diunduh.
3. **PENTING**: Sebelum mengklik "Install Now", pastikan Anda memberi centang pada kotak **"Add Python to PATH"** atau **"Add python.exe to PATH"** di bagian bawah jendela installer.
4. Klik **Install Now** dan tunggu hingga proses selesai.

### 2. Jalankan Web Server
1. Buka program **Command Prompt (CMD)** atau **PowerShell**.
2. Masuk ke direktori folder ini dengan menjalankan perintah:
   ```cmd
   cd C:\Users\Lenovo\Downloads\mancavephyton
   ```
3. Jalankan server backend Python dengan perintah:
   ```cmd
   python app.py
   ```
4. Anda akan melihat pesan:
   `Mancave Server running on http://localhost:8000`

### 3. Buka Aplikasi di Browser
1. Buka browser internet Anda (seperti Chrome, Edge, atau Firefox).
2. Masukkan alamat URL berikut di address bar:
   ```text
   http://localhost:8000
   ```
3. Aplikasi siap digunakan! Semua penambahan, pengeditan, atau penghapusan barang koleksi Anda sekarang tersimpan langsung di dalam database SQLite lokal (`mancave.db`).
