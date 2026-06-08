import os
import json
import sqlite3
import hashlib
import uuid
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8000
DB_FILE = 'mancave.db'

# In-memory session store: token -> username
sessions = {}

DEFAULT_ITEMS = [
    ("PlayStation 1 (Fat - SCPH-1000)", "Konsol Game Klasik", 1994, "MIB (Mint in Box)", 2500000, "Versi rilis pertama Jepang (SCPH-1000). Lengkap dengan box dan buku panduan asli."),
    ("Vinyl Pink Floyd - The Dark Side of the Moon", "Piringan Hitam", 1973, "Sangat Baik (VG+)", 1200000, "Piringan hitam rilis pertama Inggris (1st UK Pressing). Cover dan piringan mulus."),
    ("Jersey Tanda Tangan Michael Jordan (Bulls)", "Memorabilia Olahraga", 1998, "Sangat Baik", 15000000, "Jersey Chicago Bulls merah dengan tanda tangan Michael Jordan. Dilengkapi COA Upper Deck."),
    ("Hot Toys Iron Man Mark LXXXV (Diecast)", "Action Figure", 2020, "MISB", 6500000, "Koleksi skala 1/6 dari Avengers: Endgame. Belum pernah dibuka dari box cokelat."),
    ("Macallan Sherry Oak 18 Years Old", "Koleksi Minuman", 2021, "Baru (Segel)", 7500000, "Malt Scotch Whisky premium. Disimpan tegak lurus di dalam lemari khusus pengatur suhu."),
    ("Arcade Cabinet Vintage (Street Fighter II)", "Konsol Game Klasik", 1991, "Berfungsi Baik", 12000000, "Mesin dingdong original dengan CRT monitor 20 inci. Koin slot masih berfungsi."),
    ("Diecast Nissan Skyline GT-R R34 (1:18)", "Diecast Mobil", 2018, "Mint (Like New)", 4500000, "Skala 1:18 warna Bayside Blue. Detail mesin dan interior sangat presisi. Box lengkap."),
    ("Neon Sign \"Mancave\" Custom", "Dekorasi / Lampu", 2024, "Baru", 1500000, "Lampu LED neon flex dengan kombinasi warna biru elektrik dan merah hangat."),
    ("Kamera Analog Canon AE-1 + Lensa 50mm", "Kamera Klasik", 1976, "Berfungsi Baik", 3000000, "Kamera SLR analog legendaris. Lensa bersih bebas jamur dan lightmeter aktif."),
    ("Meja Biliar 9-Foot (Custom Oak Wood)", "Fasilitas Hiburan", 2022, "Sangat Baik", 25000000, "Bahan kayu Oak solid dengan laken wool premium warna hijau tua."),
    ("LEGO Star Wars Millennium Falcon (UCS)", "Mainan / Koleksi", 2017, "Selesai Dirakit", 13500000, "Ultimate Collector Series dengan 7.541 bagian. Dipajang di dalam lemari kaca."),
    ("Gitar Listrik Fender Stratocaster MIJ", "Alat Musik", 1995, "Sangat Baik", 14000000, "Made in Japan (MIJ) warna Sunburst. Semua part masih original bawaan pabrik.")
]

# Helper to hash password with salt
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed, salt

# Initialize database schema and data
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            year INTEGER NOT NULL,
            condition TEXT NOT NULL,
            value INTEGER NOT NULL,
            notes TEXT
        )
    ''')
    
    # Create users table for auth
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    ''')
    
    # Seed default user 'admin' with password 'admin' if empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        pw_hash, salt = hash_password('admin')
        cursor.execute('''
            INSERT INTO users (username, password_hash, salt)
            VALUES (?, ?, ?)
        ''', ('admin', pw_hash, salt))
        conn.commit()

    # Seed default items if empty
    cursor.execute('SELECT COUNT(*) FROM items')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO items (name, category, year, condition, value, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', DEFAULT_ITEMS)
        conn.commit()
        
    conn.close()

class MancaveAPIHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    # Helper to validate token
    def get_authorized_user(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        return sessions.get(token)

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        # Serve frontend files
        if self.path == '/' or self.path == '/login':
            self.path = '/index.html'
            return super().do_GET()
        
        # API GET: Fetch all items (Requires auth)
        elif self.path == '/api/items':
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
            
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items ORDER BY id DESC')
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            conn.close()
            
            return self.send_json_response(200, items)
            
        return super().do_GET()

    def do_POST(self):
        # API POST: Login
        if self.path == '/api/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            credentials = json.loads(post_data.decode('utf-8'))
            
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not username or not password:
                return self.send_json_response(400, {'error': 'Username dan password diperlukan'})
                
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                stored_hash, salt = row
                test_hash, _ = hash_password(password, salt)
                if test_hash == stored_hash:
                    # Login success: generate session token
                    token = str(uuid.uuid4())
                    sessions[token] = username
                    return self.send_json_response(200, {'token': token, 'username': username})
            
            return self.send_json_response(401, {'error': 'Username atau password salah'})

        # API POST: Logout
        elif self.path == '/api/logout':
            auth_header = self.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                if token in sessions:
                    del sessions[token]
            return self.send_json_response(200, {'success': True})

        # API POST: Change Password (Requires auth)
        elif self.path == '/api/change-password':
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            pwd_data = json.loads(post_data.decode('utf-8'))
            
            old_password = pwd_data.get('old_password')
            new_password = pwd_data.get('new_password')
            
            if not old_password or not new_password:
                return self.send_json_response(400, {'error': 'Semua field password diperlukan'})
                
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash, salt FROM users WHERE username = ?', (user,))
            row = cursor.fetchone()
            
            if row:
                stored_hash, salt = row
                test_hash, _ = hash_password(old_password, salt)
                if test_hash == stored_hash:
                    # Update with new salt and hash
                    new_hash, new_salt = hash_password(new_password)
                    cursor.execute('''
                        UPDATE users
                        SET password_hash = ?, salt = ?
                        WHERE username = ?
                    ''', (new_hash, new_salt, user))
                    conn.commit()
                    conn.close()
                    return self.send_json_response(200, {'success': True, 'message': 'Password berhasil diganti'})
            
            conn.close()
            return self.send_json_response(400, {'error': 'Password lama salah'})

        # API POST: Add new item (Requires auth)
        elif self.path == '/api/items':
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            item_data = json.loads(post_data.decode('utf-8'))
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (name, category, year, condition, value, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item_data['name'],
                item_data['category'],
                int(item_data['year']),
                item_data['condition'],
                int(item_data['value']),
                item_data['notes']
            ))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            item_data['id'] = new_id
            return self.send_json_response(201, item_data)
        
        # API POST: Reset database (Requires auth)
        elif self.path == '/api/reset':
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
                
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items')
            cursor.executemany('''
                INSERT INTO items (name, category, year, condition, value, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', DEFAULT_ITEMS)
            conn.commit()
            
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items ORDER BY id DESC')
            rows = cursor.fetchall()
            items = [dict(row) for row in rows]
            conn.close()
            
            return self.send_json_response(200, items)

    def do_PUT(self):
        # API PUT: Update item (Requires auth)
        if self.path.startswith('/api/items/'):
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
                
            item_id = int(self.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)
            item_data = json.loads(put_data.decode('utf-8'))
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE items
                SET name = ?, category = ?, year = ?, condition = ?, value = ?, notes = ?
                WHERE id = ?
            ''', (
                item_data['name'],
                item_data['category'],
                int(item_data['year']),
                item_data['condition'],
                int(item_data['value']),
                item_data['notes'],
                item_id
            ))
            conn.commit()
            conn.close()
            
            item_data['id'] = item_id
            return self.send_json_response(200, item_data)

    def do_DELETE(self):
        # API DELETE: Delete item (Requires auth)
        if self.path.startswith('/api/items/'):
            user = self.get_authorized_user()
            if not user:
                return self.send_json_response(401, {'error': 'Unauthorized'})
                
            item_id = int(self.path.split('/')[-1])
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            
            return self.send_json_response(200, {'success': True})

def run():
    init_db()
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, MancaveAPIHandler)
    print(f"Mancave Server running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
