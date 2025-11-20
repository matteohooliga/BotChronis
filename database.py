import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import config

class ChronosDatabase:
    def __init__(self, db_name: str = config.DATABASE_NAME):
        self.db_name = db_name

    async def initialize_database(self):
        async with aiosqlite.connect(self.db_name) as db:
            # Table Sessions
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    guild_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER,
                    pause_duration INTEGER DEFAULT 0,
                    total_duration INTEGER,
                    is_active INTEGER DEFAULT 1,
                    is_paused INTEGER DEFAULT 0,
                    pause_start INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)

            # Table Config
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    message_id TEXT,
                    log_channel_id TEXT,
                    direction_role_id TEXT,
                    auto_roles_list TEXT,
                    min_hours_goal INTEGER DEFAULT 0,
                    is_maintenance INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'fr',
                    allowed_roles TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Migrations de sécurité (Ajout colonnes manquantes si update)
            cols = ["log_channel_id", "direction_role_id", "auto_roles_list", "min_hours_goal", "is_maintenance", "language"]
            for col in cols:
                try: await db.execute(f"ALTER TABLE guild_config ADD COLUMN {col} TEXT")
                except: pass
            
            await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, guild_id, is_active)")
            await db.commit()

    # --- SESSIONS ---
    async def start_session(self, user_id, guild_id, username):
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            cur = await db.execute("INSERT INTO sessions (user_id, guild_id, username, start_time) VALUES (?, ?, ?, ?)", (user_id, guild_id, username, now))
            await db.commit()
            return cur.lastrowid

    async def get_active_session(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE user_id = ? AND guild_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1", (user_id, guild_id)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_all_active_sessions(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE guild_id = ? AND is_active = 1 ORDER BY start_time DESC", (guild_id,)) as cur:
                return [dict(row) for row in await cur.fetchall()]

    async def pause_session(self, user_id, guild_id):
        session = await self.get_active_session(user_id, guild_id)
        if not session or session['is_paused']: return False
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE sessions SET is_paused = 1, pause_start = ? WHERE id = ?", (now, session['id']))
            await db.commit()
        return True

    async def resume_session(self, user_id, guild_id):
        session = await self.get_active_session(user_id, guild_id)
        if not session or not session['is_paused']: return False
        now = int(datetime.now().timestamp() * 1000)
        pause_dur = now - session['pause_start']
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE sessions SET is_paused = 0, pause_start = NULL, pause_duration = pause_duration + ? WHERE id = ?", (pause_dur, session['id']))
            await db.commit()
        return True

    async def end_session(self, user_id, guild_id):
        session = await self.get_active_session(user_id, guild_id)
        if not session: return None
        now = int(datetime.now().timestamp() * 1000)
        total = now - session['start_time']
        if session['is_paused'] and session['pause_start']:
            cur_p = now - session['pause_start']
            total -= (session['pause_duration'] + cur_p)
            total_pause = session['pause_duration'] + cur_p
        else:
            total -= session['pause_duration']
            total_pause = session['pause_duration']
        
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("UPDATE sessions SET end_time = ?, total_duration = ?, pause_duration = ?, is_active = 0, is_paused = 0, pause_start = NULL WHERE id = ?", (now, total, total_pause, session['id']))
            await db.commit()
        return {**session, 'total_duration': total, 'pause_duration': total_pause, 'end_time': now}

    async def add_time_adjustment(self, user_id, guild_id, username, duration_ms):
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("INSERT INTO sessions (user_id, guild_id, username, start_time, end_time, total_duration, is_active, is_paused) VALUES (?, ?, ?, ?, ?, ?, 0, 0)", (user_id, guild_id, username, now, now, duration_ms))
            await db.commit()

    # --- STATS ---
    async def get_user_stats(self, user_id, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT username, COUNT(*) as total_sessions, SUM(total_duration) as total_time, AVG(total_duration) as avg_time, MAX(total_duration) as max_time, MIN(total_duration) as min_time FROM sessions WHERE user_id = ? AND guild_id = ? AND is_active = 0 GROUP BY user_id", (user_id, guild_id)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_all_users_stats(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, username, COUNT(*) as total_sessions, SUM(total_duration) as total_time, AVG(total_duration) as avg_time FROM sessions WHERE guild_id = ? AND is_active = 0 GROUP BY user_id ORDER BY total_time DESC", (guild_id,)) as cur:
                return [dict(row) for row in await cur.fetchall()]

    async def get_last_sessions(self, user_id, guild_id, limit):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE user_id = ? AND guild_id = ? AND is_active = 0 ORDER BY start_time DESC LIMIT ?", (user_id, guild_id, limit)) as cur:
                return [dict(row) for row in await cur.fetchall()]

    async def get_total_active_sessions_count(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    # --- DELETE / RESET ---
    async def reset_guild_data(self, guild_id, time_window_ms=None):
        async with aiosqlite.connect(self.db_name) as db:
            if time_window_ms:
                limit = int(datetime.now().timestamp() * 1000) - time_window_ms
                cur = await db.execute("DELETE FROM sessions WHERE guild_id = ? AND start_time >= ?", (guild_id, limit))
            else:
                cur = await db.execute("DELETE FROM sessions WHERE guild_id = ?", (guild_id,))
            deleted = cur.rowcount
            await db.commit()
            return deleted

    async def delete_user_data(self, guild_id, user_id):
        async with aiosqlite.connect(self.db_name) as db:
            cur = await db.execute("DELETE FROM sessions WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            deleted = cur.rowcount
            await db.commit()
            return deleted

    # --- CONFIG ---
    async def set_guild_config(self, guild_id, channel_id, message_id, log_channel_id=None, language='fr', direction_role_id=None, min_hours_goal=0, auto_roles_list=None):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                INSERT INTO guild_config (guild_id, channel_id, message_id, log_channel_id, language, direction_role_id, min_hours_goal, auto_roles_list, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%s', 'now'))
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    message_id = excluded.message_id,
                    log_channel_id = excluded.log_channel_id,
                    language = excluded.language,
                    direction_role_id = excluded.direction_role_id,
                    min_hours_goal = excluded.min_hours_goal,
                    auto_roles_list = excluded.auto_roles_list,
                    updated_at = strftime('%s', 'now')
            """, (guild_id, channel_id, message_id, log_channel_id, language, direction_role_id, min_hours_goal, auto_roles_list))
            await db.commit()

    async def set_maintenance(self, guild_id, active):
        async with aiosqlite.connect(self.db_name) as db:
            val = 1 if active else 0
            await db.execute("UPDATE guild_config SET is_maintenance = ? WHERE guild_id = ?", (val, str(guild_id)))
            await db.commit()

    async def get_guild_config(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_all_guild_configs(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM guild_config") as cur:
                return [dict(row) for row in await cur.fetchall()]