"""Persistent online accounts. Passwords and bearer sessions are never stored plain."""
import hashlib
import os
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path

class Accounts:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            descriptor=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(descriptor)
        except FileExistsError:
            pass
        self.lock = threading.Lock()
        self.attempts = {}
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, salt TEXT NOT NULL,
                digest TEXT NOT NULL, created INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (digest TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);''')
    def connect(self):
        return sqlite3.connect(self.path, timeout=10)
    @staticmethod
    def digest(password, salt):
        return hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
    def limit(self, address):
        now = time.time()
        with self.lock:
            self.attempts = {k: [t for t in v if t > now-900] for k,v in self.attempts.items() if any(t > now-900 for t in v)}
            attempts = self.attempts.setdefault(address, [])
            if len(attempts) >= 15: raise ValueError('Too many attempts. Try again in 15 minutes.')
            attempts.append(now)
    def register(self, data):
        email = str(data.get('email','')).strip().lower()
        password = str(data.get('password',''))
        name = str(data.get('name','')).strip()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email)>254: raise ValueError('Enter a valid email address.')
        if not 10 <= len(password) <= 128: raise ValueError('Use a password of 10 to 128 characters.')
        if not 1 <= len(name) <= 100: raise ValueError('Enter your name (up to 100 characters).')
        salt = secrets.token_hex(16)
        digest = self.digest(password, salt)
        try:
            with self.connect() as db:
                db.execute('INSERT INTO users(email,name,salt,digest,created) VALUES(?,?,?,?,?)', (email,name,salt,digest,int(time.time())))
        except sqlite3.IntegrityError:
            raise ValueError('An account already uses this email. Sign in instead.') from None
        return self.login(data)
    def login(self, data):
        email = str(data.get('email','')).strip().lower()
        password = str(data.get('password',''))
        if len(password)>128: raise ValueError('Email or password is incorrect.')
        with self.connect() as db:
            row=db.execute('SELECT id,name,email,salt,digest FROM users WHERE email=?', (email,)).fetchone()
            salt = row[3] if row else '00'*16
            actual=self.digest(password,salt)
            if not row or not secrets.compare_digest(actual,row[4]): raise ValueError('Email or password is incorrect.')
            token=secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<?',(int(time.time()),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row[0],int(time.time())+604800))
        return token, {'name':row[1], 'email':row[2]}
    def user(self, token):
        if not token: return None
        with self.connect() as db:
            row=db.execute('SELECT users.name,users.email FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.digest=? AND sessions.expires>?', (hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
        return {'name':row[0],'email':row[1]} if row else None
    def logout(self, token):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE digest=?',(hashlib.sha256(token.encode()).hexdigest(),))
