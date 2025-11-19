import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import config

class ChronosDatabase:
    def __init__(self, db_name: str = config.DATABASE_NAME):
        self.db_name = db_name

    async def initialize_database(self):
        """Initialiser les tables de la base de données (Async)"""
        async with aiosqlite.connect(self.db_name) as db:
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

            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    message_id TEXT,
                    log_channel_id TEXT,
                    allowed_roles TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Migration pour les anciennes DB
            try:
                await db.execute("ALTER TABLE guild_config ADD COLUMN log_channel_id TEXT")
            except:
                pass

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user 
                ON sessions(user_id, guild_id, is_active)
            """)
            await db.commit()

    # ===== GESTION DES SESSIONS =====

    async def start_session(self, user_id: str, guild_id: str, username: str) -> int:
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("""
                INSERT INTO sessions (user_id, guild_id, username, start_time)
                VALUES (?, ?, ?, ?)
            """, (user_id, guild_id, username, now))
            await db.commit()
            return cursor.lastrowid

    async def get_active_session(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sessions 
                WHERE user_id = ? AND guild_id = ? AND is_active = 1
                ORDER BY id DESC LIMIT 1
            """, (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_active_sessions(self, guild_id: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM sessions 
                WHERE guild_id = ? AND is_active = 1
                ORDER BY start_time DESC
            """, (guild_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def pause_session(self, user_id: str, guild_id: str) -> bool:
        session = await self.get_active_session(user_id, guild_id)
        if not session or session['is_paused']:
            return False

        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                UPDATE sessions 
                SET is_paused = 1, pause_start = ?
                WHERE id = ?
            """, (now, session['id']))
            await db.commit()
        return True

    async def resume_session(self, user_id: str, guild_id: str) -> bool:
        session = await self.get_active_session(user_id, guild_id)
        if not session or not session['is_paused']:
            return False

        now = int(datetime.now().timestamp() * 1000)
        pause_duration = now - session['pause_start']
        
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                UPDATE sessions 
                SET is_paused = 0, 
                    pause_start = NULL,
                    pause_duration = pause_duration + ?
                WHERE id = ?
            """, (pause_duration, session['id']))
            await db.commit()
        return True

    async def end_session(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        session = await self.get_active_session(user_id, guild_id)
        if not session:
            return None

        now = int(datetime.now().timestamp() * 1000)
        total_duration = now - session['start_time']
        
        if session['is_paused'] and session['pause_start']:
            current_pause_duration = now - session['pause_start']
            total_duration -= (session['pause_duration'] + current_pause_duration)
            total_pause = session['pause_duration'] + current_pause_duration
        else:
            total_duration -= session['pause_duration']
            total_pause = session['pause_duration']

        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                UPDATE sessions 
                SET end_time = ?,
                    total_duration = ?,
                    pause_duration = ?,
                    is_active = 0,
                    is_paused = 0,
                    pause_start = NULL
                WHERE id = ?
            """, (now, total_duration, total_pause, session['id']))
            await db.commit()
        
        return {
            **session,
            'total_duration': total_duration,
            'pause_duration': total_pause,
            'end_time': now
        }

    # ===== AJOUT DE TEMPS MANUEL (Pour /edittime) =====

    async def add_time_adjustment(self, user_id: str, guild_id: str, username: str, duration_ms: int):
        """Ajoute (ou retire) du temps de service manuellement"""
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            # On insère une session "fantôme" terminée pour ajuster le total
            await db.execute("""
                INSERT INTO sessions (user_id, guild_id, username, start_time, end_time, total_duration, is_active, is_paused)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """, (user_id, guild_id, username, now, now, duration_ms))
            await db.commit()

    # ===== STATISTIQUES =====

    async def get_user_stats(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    username,
                    COUNT(*) as total_sessions,
                    SUM(total_duration) as total_time,
                    AVG(total_duration) as avg_time,
                    MAX(total_duration) as max_time,
                    MIN(total_duration) as min_time
                FROM sessions 
                WHERE user_id = ? AND guild_id = ? AND is_active = 0
                GROUP BY user_id
            """, (user_id, guild_id)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_users_stats(self, guild_id: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT 
                    user_id,
                    username,
                    COUNT(*) as total_sessions,
                    SUM(total_duration) as total_time,
                    AVG(total_duration) as avg_time
                FROM sessions 
                WHERE guild_id = ? AND is_active = 0
                GROUP BY user_id
                ORDER BY total_time DESC
            """, (guild_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== CONFIGURATION =====

    async def set_guild_config(self, guild_id: str, channel_id: str, message_id: str, log_channel_id: str = None):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                INSERT INTO guild_config (guild_id, channel_id, message_id, log_channel_id, updated_at)
                VALUES (?, ?, ?, ?, strftime('%s', 'now'))
                ON CONFLICT(guild_id) DO UPDATE SET
                    channel_id = excluded.channel_id,
                    message_id = excluded.message_id,
                    log_channel_id = excluded.log_channel_id,
                    updated_at = strftime('%s', 'now')
            """, (guild_id, channel_id, message_id, log_channel_id))
            await db.commit()

    async def get_guild_config(self, guild_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM guild_config WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_guild_configs(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM guild_config") as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def reset_guild_stats(self, guild_id: str) -> int:
        # CORRECTION ICI : Suppression du code dupliqué erroné
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("DELETE FROM sessions WHERE guild_id = ?", (guild_id,))
            deleted = cursor.rowcount
            await db.commit()
            return deleted