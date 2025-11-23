import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict
import config

class ChronosDatabase:
    def __init__(self, db_name: str = config.DATABASE_NAME):
        self.db_name = db_name

    async def initialize_database(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, guild_id TEXT, username TEXT, start_time INTEGER, end_time INTEGER, pause_duration INTEGER DEFAULT 0, total_duration INTEGER, is_active INTEGER DEFAULT 1, is_paused INTEGER DEFAULT 0, pause_start INTEGER, created_at INTEGER DEFAULT (strftime('%s', 'now')))")
            await db.execute("CREATE TABLE IF NOT EXISTS guild_config (guild_id TEXT PRIMARY KEY, channel_id TEXT, message_id TEXT, log_channel_id TEXT, direction_role_id TEXT, auto_roles_list TEXT, min_hours_goal INTEGER DEFAULT 0, is_maintenance INTEGER DEFAULT 0, language TEXT DEFAULT 'fr', allowed_roles TEXT, created_at INTEGER, updated_at INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id TEXT PRIMARY KEY)")
            
            cols = ["log_channel_id", "direction_role_id", "auto_roles_list", "min_hours_goal", "is_maintenance", "language"]
            for col in cols:
                try: await db.execute(f"ALTER TABLE guild_config ADD COLUMN {col} TEXT")
                except: pass
            await db.commit()

    # --- STATISTIQUES AVANCÉES (Nouvelle Logique) ---
    async def get_advanced_server_stats(self, guild_id):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            # Récupérer uniquement les sessions terminées pour les stats historiques
            async with db.execute("SELECT user_id, total_duration, start_time FROM sessions WHERE guild_id = ? AND is_active = 0", (guild_id,)) as cur:
                rows = await cur.fetchall()
            
            if not rows: return None

            # Structures pour l'agrégation
            daily_stats = defaultdict(lambda: {'users': set(), 'duration': 0})
            weekly_stats = defaultdict(lambda: {'users': set(), 'duration': 0})
            total_duration_global = 0
            
            for r in rows:
                duration = r['total_duration'] or 0
                uid = r['user_id']
                
                # Conversion Timestamp -> Date
                dt = datetime.fromtimestamp(r['start_time'] / 1000)
                day_key = dt.date() # Ex: 2023-11-21
                week_key = f"{dt.year}-{dt.isocalendar()[1]}" # Ex: 2023-47
                
                # Agrégation Jour
                daily_stats[day_key]['users'].add(uid)
                daily_stats[day_key]['duration'] += duration
                
                # Agrégation Semaine
                weekly_stats[week_key]['users'].add(uid)
                weekly_stats[week_key]['duration'] += duration
                
                total_duration_global += duration

            # Calculs finaux
            days_count = len(daily_stats)
            weeks_count = len(weekly_stats)
            
            # 1. Moyenne de personnes en service par jour
            # Somme des utilisateurs uniques chaque jour / Nombre de jours
            sum_users_per_day = sum(len(d['users']) for d in daily_stats.values())
            avg_people_per_day = sum_users_per_day / days_count if days_count > 0 else 0
            
            # 2. Temps moyen de service par utilisateur par jour
            # On prend la durée totale du jour divisée par le nombre d'utilisateurs ce jour-là, puis on fait la moyenne de tout ça
            daily_averages = []
            for d in daily_stats.values():
                if len(d['users']) > 0:
                    daily_averages.append(d['duration'] / len(d['users']))
            avg_time_user_day = (sum(daily_averages) / len(daily_averages)) if daily_averages else 0
            
            # 3. Temps moyen de service par utilisateur par semaine
            weekly_averages = []
            for w in weekly_stats.values():
                if len(w['users']) > 0:
                    weekly_averages.append(w['duration'] / len(w['users']))
            avg_time_user_week = (sum(weekly_averages) / len(weekly_averages)) if weekly_averages else 0

            return {
                "total_sessions": len(rows),
                "total_duration": total_duration_global,
                "days_analyzed": days_count,
                "avg_people_per_day": avg_people_per_day,
                "avg_time_user_day": avg_time_user_day,
                "avg_time_user_week": avg_time_user_week
            }

    # --- FONCTIONS STANDARDS ---

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

    async def get_user_stats(self, user_id, guild_id):
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT username, COUNT(*) as total_sessions, SUM(total_duration) as total_time, AVG(total_duration) as avg_time, MAX(total_duration) as max_time, MIN(total_duration) as min_time FROM sessions WHERE user_id = ? AND guild_id = ? AND is_active = 0 GROUP BY user_id", (user_id, guild_id)) as cur:
                row = await cur.fetchone()
                stats = dict(row) if row else {'username': 'Unknown', 'total_sessions': 0, 'total_time': 0, 'avg_time': 0, 'max_time': 0, 'min_time': 0}
            async with db.execute("SELECT * FROM sessions WHERE user_id = ? AND guild_id = ? AND is_active = 1", (user_id, guild_id)) as cur:
                active = await cur.fetchone()
                if active:
                    current_duration = (active['pause_start'] - active['start_time'] - active['pause_duration']) if active['is_paused'] else (now - active['start_time'] - active['pause_duration'])
                    stats['total_time'] = (stats['total_time'] or 0) + current_duration
            return stats

    async def get_all_users_stats(self, guild_id):
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, username, total_duration FROM sessions WHERE guild_id = ? AND is_active = 0", (guild_id,)) as cur:
                rows = await cur.fetchall()
            async with db.execute("SELECT user_id, username, start_time, pause_duration, is_paused, pause_start FROM sessions WHERE guild_id = ? AND is_active = 1", (guild_id,)) as cur:
                active_rows = await cur.fetchall()
            user_stats = {}
            for r in rows:
                uid = r['user_id']
                if uid not in user_stats: user_stats[uid] = {'username': r['username'], 'total_sessions': 0, 'total_time': 0}
                user_stats[uid]['total_sessions'] += 1
                user_stats[uid]['total_time'] += (r['total_duration'] or 0)
            for r in active_rows:
                uid = r['user_id']
                if uid not in user_stats: user_stats[uid] = {'username': r['username'], 'total_sessions': 0, 'total_time': 0}
                current_duration = (r['pause_start'] - r['start_time'] - r['pause_duration']) if r['is_paused'] else (now - r['start_time'] - r['pause_duration'])
                user_stats[uid]['total_time'] += current_duration
            result = []
            for uid, data in user_stats.items():
                result.append({'user_id': uid, 'username': data['username'], 'total_sessions': data['total_sessions'], 'total_time': data['total_time']})
            return sorted(result, key=lambda x: x['total_time'], reverse=True)

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
            
    async def set_global_maintenance(self, active):
        async with aiosqlite.connect(self.db_name) as db:
            val = 1 if active else 0
            await db.execute("UPDATE guild_config SET is_maintenance = ?", (val,))
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

    # --- BLACKLIST ---
    async def add_blacklist(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def remove_blacklist(self, user_id: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))
            await db.commit()

    async def is_blacklisted(self, user_id: str) -> bool:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,)) as cur:
                return await cur.fetchone() is not None