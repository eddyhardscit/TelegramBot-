from __future__ import annotations
import sqlite3, threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class UserProfile:
    telegram_id:int; username:Optional[str]; first_name:Optional[str]; last_name:Optional[str]; preferred_name:Optional[str]; first_seen:str; last_seen:str; message_count:int

class MemoryStore:
    def __init__(self, db_path:str="data/arena_memory.sqlite3"):
        self.db_path=Path(db_path); self.db_path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.Lock(); self._init_db()
    def _connect(self):
        c=sqlite3.connect(self.db_path,timeout=20); c.row_factory=sqlite3.Row; return c
    def _init_db(self):
        with self._lock,self._connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,last_name TEXT,preferred_name TEXT,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,message_count INTEGER NOT NULL DEFAULT 0)""")
            c.execute("""CREATE TABLE IF NOT EXISTS memories(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER NOT NULL,memory_key TEXT NOT NULL,memory_value TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(telegram_id,memory_key))""")
            c.commit()
    def touch_user(self,telegram_id,username,first_name,last_name):
        now=datetime.now(timezone.utc).isoformat()
        with self._lock,self._connect() as c:
            row=c.execute('SELECT * FROM users WHERE telegram_id=?',(telegram_id,)).fetchone(); is_new=row is None
            if is_new:
                c.execute('INSERT INTO users VALUES(?,?,?,?,NULL,?,?,1)',(telegram_id,username,first_name,last_name,now,now))
            else:
                c.execute('UPDATE users SET username=?,first_name=?,last_name=?,last_seen=?,message_count=message_count+1 WHERE telegram_id=?',(username,first_name,last_name,now,telegram_id))
            c.commit(); row=c.execute('SELECT * FROM users WHERE telegram_id=?',(telegram_id,)).fetchone()
        return self._row(row),is_new
    def get_user(self,telegram_id):
        with self._lock,self._connect() as c: row=c.execute('SELECT * FROM users WHERE telegram_id=?',(telegram_id,)).fetchone()
        return self._row(row) if row else None
    def set_preferred_name(self,telegram_id,name):
        name=name.strip()[:50]
        if not name: raise ValueError('empty name')
        with self._lock,self._connect() as c: c.execute('UPDATE users SET preferred_name=? WHERE telegram_id=?',(name,telegram_id)); c.commit()
    def forget_user(self,telegram_id):
        with self._lock,self._connect() as c: c.execute('DELETE FROM memories WHERE telegram_id=?',(telegram_id,)); c.execute('DELETE FROM users WHERE telegram_id=?',(telegram_id,)); c.commit()
    @staticmethod
    def display_name(p): return p.preferred_name or p.first_name or p.username or 'Champion'
    @staticmethod
    def _row(r): return UserProfile(int(r['telegram_id']),r['username'],r['first_name'],r['last_name'],r['preferred_name'],str(r['first_seen']),str(r['last_seen']),int(r['message_count']))
