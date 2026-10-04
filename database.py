import aiomysql
import json
import time
from datetime import datetime, timedelta
import config
from utils import format_duration 

class ChronosDatabase:
    def __init__(self):
        self.pool = None
        self._config_cache = {} 

    async def get_pool(self):
        if not self.pool:
            self.pool = await aiomysql.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                db=config.DB_NAME,
                autocommit=True,
                cursorclass=aiomysql.DictCursor 
            )
        return self.pool

    async def close_pool(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def _execute(self, query, args=None):
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return cur.lastrowid, cur.rowcount

    async def _fetch(self, query, args=None, one=False):
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return await cur.fetchone() if one else await cur.fetchall()

    async def initialize_database(self):
        queries = [
            """CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255) NOT NULL, guild_id VARCHAR(255) NOT NULL,
                username VARCHAR(255), start_time BIGINT, start_time_human VARCHAR(50), end_time BIGINT,
                end_time_human VARCHAR(50), pause_duration BIGINT DEFAULT 0, pause_duration_human VARCHAR(50),
                total_duration BIGINT, total_duration_human VARCHAR(50), is_active TINYINT DEFAULT 1,
                is_paused TINYINT DEFAULT 0, pause_start BIGINT, created_at BIGINT
            )""",
            """CREATE TABLE IF NOT EXISTS guild_config (
                guild_id VARCHAR(255) PRIMARY KEY, channel_id VARCHAR(255), message_id VARCHAR(255),
                log_channel_id VARCHAR(255), direction_role_id TEXT, auto_roles_list TEXT,
                citizen_role_id VARCHAR(255), min_hours_goal INT DEFAULT 0, is_maintenance TINYINT DEFAULT 0,
                language VARCHAR(10) DEFAULT 'fr', allowed_roles TEXT, created_at BIGINT, updated_at BIGINT,
                updated_at_human VARCHAR(50), rdv_channel_public VARCHAR(255), rdv_channel_staff VARCHAR(255),
                rdv_channel_transcript VARCHAR(255), rdv_message_id VARCHAR(255), rdv_role_staff VARCHAR(255),
                rdv_types TEXT
            )""",
            "CREATE TABLE IF NOT EXISTS blacklist (user_id VARCHAR(255) PRIMARY KEY, username VARCHAR(255))",
            """CREATE TABLE IF NOT EXISTS absences (
                id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(255), username VARCHAR(255),
                guild_id VARCHAR(255), start_date VARCHAR(20), end_date VARCHAR(20), reason TEXT, message_id VARCHAR(255)
            )""",
            """CREATE TABLE IF NOT EXISTS employee_dates (
                guild_id VARCHAR(255) NOT NULL, user_id VARCHAR(255) NOT NULL, job_date BIGINT NOT NULL, PRIMARY KEY (guild_id, user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS weekly_runs (
                guild_id VARCHAR(255) NOT NULL, run_date DATE NOT NULL,
                status VARCHAR(16) NOT NULL, total_ms BIGINT NOT NULL DEFAULT 0,
                cutoff_ms BIGINT NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, run_date)
            )""",
            """CREATE TABLE IF NOT EXISTS bot_state (
                state_key VARCHAR(64) PRIMARY KEY, state_value VARCHAR(255) NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS manual_premium (
                guild_id VARCHAR(255) PRIMARY KEY,
                granted_by VARCHAR(255) NOT NULL,
                granted_at BIGINT NOT NULL
            )"""
        ]
        for q in queries:
            try:
                await self._execute(q)
            except Exception as e:
                raise RuntimeError(f"Initialisation de la base impossible: {e}") from e

        # MySQL ne prend pas en charge CREATE INDEX IF NOT EXISTS sur toutes les versions.
        for name, columns in (
            ("idx_sessions_active", "guild_id, is_active"),
            ("idx_sessions_user", "user_id, guild_id"),
            ("idx_sessions_start", "start_time"),
        ):
            row = await self._fetch(
                "SELECT 1 FROM information_schema.statistics WHERE table_schema = DATABASE() "
                "AND table_name = 'sessions' AND index_name = %s LIMIT 1", (name,), one=True
            )
            if not row:
                await self._execute(f"CREATE INDEX {name} ON sessions({columns})")

        # Ajouter uniquement les colonnes absentes ; toute autre erreur doit être visible.
        columns = await self._fetch(
            "SELECT column_name AS name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'guild_config'"
        )
        existing = {row['name'] for row in columns}
        for name, definition in (
            ('service_role_id', 'VARCHAR(255)'),
            ('embed_color', 'VARCHAR(10) DEFAULT NULL'),
            ('auto_purge_day', 'INT DEFAULT -1'),
            ('auto_purge_time', "VARCHAR(5) DEFAULT '00:00'"),
        ):
            if name not in existing:
                await self._execute(f'ALTER TABLE guild_config ADD COLUMN {name} {definition}')

    async def set_auto_purge(self, guild_id, day_int, time_str):
        self._config_cache.pop(str(guild_id), None)
        await self._execute("INSERT IGNORE INTO guild_config (guild_id) VALUES (%s)", (str(guild_id),))
        now = int(time.time())
        await self._execute("UPDATE guild_config SET auto_purge_day = %s, auto_purge_time = %s, updated_at = %s WHERE guild_id = %s", (day_int, time_str, now, str(guild_id)))

    async def get_weekly_run(self, guild_id, run_date):
        return await self._fetch("SELECT * FROM weekly_runs WHERE guild_id = %s AND run_date = %s", (str(guild_id), run_date), one=True)

    async def get_previous_weekly_total(self, guild_id, run_date):
        row = await self._fetch("SELECT total_ms FROM weekly_runs WHERE guild_id = %s AND run_date < %s AND status IN ('sent', 'done') ORDER BY run_date DESC LIMIT 1", (str(guild_id), run_date), one=True)
        return int(row['total_ms']) if row else 0

    async def set_weekly_run(self, guild_id, run_date, status, total_ms, cutoff_ms):
        await self._execute("INSERT INTO weekly_runs (guild_id, run_date, status, total_ms, cutoff_ms) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE status = VALUES(status), total_ms = VALUES(total_ms), cutoff_ms = VALUES(cutoff_ms)", (str(guild_id), run_date, status, int(total_ms), int(cutoff_ms)))

    async def reset_weekly_data(self, guild_id, cutoff_ms):
        await self._execute("DELETE FROM sessions WHERE guild_id = %s AND start_time <= %s AND is_active = 0", (str(guild_id), int(cutoff_ms)))

    async def set_custom_color(self, guild_id, hex_color):
        self._config_cache.pop(str(guild_id), None)
        await self._execute("INSERT IGNORE INTO guild_config (guild_id) VALUES (%s)", (str(guild_id),))
        await self._execute("UPDATE guild_config SET embed_color = %s WHERE guild_id = %s", (hex_color, str(guild_id)))

    async def set_employee_date(self, guild_id, user_id, timestamp):
        await self._execute("INSERT INTO employee_dates (guild_id, user_id, job_date) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE job_date = VALUES(job_date)", (str(guild_id), str(user_id), int(timestamp)))

    async def get_employees_dates(self, guild_id):
        rows = await self._fetch("SELECT user_id, job_date FROM employee_dates WHERE guild_id = %s", (str(guild_id),))
        return {r['user_id']: r['job_date'] for r in rows}

    async def add_absence(self, user_id, username, guild_id, start_date_str, end_date_str, reason, message_id=None):
        await self._execute("INSERT INTO absences (user_id, username, guild_id, start_date, end_date, reason, message_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", (str(user_id), str(username), str(guild_id), start_date_str, end_date_str, reason, str(message_id) if message_id else None))

    async def end_absence(self, message_id):
        await self._execute("DELETE FROM absences WHERE message_id = %s", (str(message_id),))

    async def get_absence_by_message_id(self, message_id):
        return await self._fetch("SELECT * FROM absences WHERE message_id = %s", (str(message_id),), one=True)

    async def delete_expired_absences(self):
        await self._execute("DELETE FROM absences WHERE STR_TO_DATE(end_date, '%d/%m/%Y') < CURDATE()")

    async def get_absent_users(self, guild_id):
        rows = await self._fetch("SELECT user_id FROM absences WHERE guild_id = %s AND CURDATE() BETWEEN STR_TO_DATE(start_date, '%%d/%%m/%%Y') AND STR_TO_DATE(end_date, '%%d/%%m/%%Y')", (str(guild_id),))
        return [str(r['user_id']) for r in rows]

    async def get_active_absences_details(self, guild_id):
        return await self._fetch("SELECT user_id, username, start_date, end_date, reason FROM absences WHERE guild_id = %s AND CURDATE() BETWEEN STR_TO_DATE(start_date, '%%d/%%m/%%Y') AND STR_TO_DATE(end_date, '%%d/%%m/%%Y')", (str(guild_id),))

    async def set_rdv_config(self, guild_id, public_id, staff_id, transcript_id, role_id, types, message_id=None):
        self._config_cache.pop(str(guild_id), None)
        await self._execute("INSERT IGNORE INTO guild_config (guild_id) VALUES (%s)", (str(guild_id),))
        now_ts = int(datetime.now().timestamp())
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        if message_id:
            await self._execute("UPDATE guild_config SET rdv_channel_public=%s, rdv_channel_staff=%s, rdv_channel_transcript=%s, rdv_role_staff=%s, rdv_types=%s, rdv_message_id=%s, updated_at=%s, updated_at_human=%s WHERE guild_id=%s", (str(public_id), str(staff_id), str(transcript_id), str(role_id), json.dumps(types), str(message_id), now_ts, now_str, str(guild_id)))
        else:
            await self._execute("UPDATE guild_config SET rdv_channel_public=%s, rdv_channel_staff=%s, rdv_channel_transcript=%s, rdv_role_staff=%s, rdv_types=%s, updated_at=%s, updated_at_human=%s WHERE guild_id=%s", (str(public_id), str(staff_id), str(transcript_id), str(role_id), json.dumps(types), now_ts, now_str, str(guild_id)))

    async def get_rdv_config(self, guild_id):
        r = await self._fetch("SELECT rdv_channel_public, rdv_channel_staff, rdv_channel_transcript, rdv_role_staff, rdv_types, rdv_message_id FROM guild_config WHERE guild_id = %s", (str(guild_id),), one=True)
        if r: return {'public': r['rdv_channel_public'], 'staff': r['rdv_channel_staff'], 'transcript': r['rdv_channel_transcript'], 'role': r['rdv_role_staff'], 'types': json.loads(r['rdv_types']) if r['rdv_types'] else [], 'message_id': r['rdv_message_id']}
        return {'public': None, 'staff': None, 'transcript': None, 'role': None, 'types': [], 'message_id': None}

    async def get_sessions_history(self, guild_id, days=7):
        limit = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        return await self._fetch("SELECT * FROM sessions WHERE guild_id = %s AND is_active = 0 AND start_time > %s", (str(guild_id), limit))

    async def get_advanced_server_stats(self, guild_id):
        rows = await self._fetch("SELECT user_id, total_duration, start_time FROM sessions WHERE guild_id = %s AND is_active = 0", (str(guild_id),))
        if not rows: return None
        total = sum((r['total_duration'] or 0) for r in rows)
        unique = len(set(r['user_id'] for r in rows))
        dates = set(datetime.fromtimestamp(r['start_time']/1000).date() for r in rows)
        days = len(dates) if dates else 1
        return {"total_sessions": len(rows), "total_duration": total, "unique_users": unique, "days_analyzed": days, "avg_people_per_day": unique / days, "avg_time_user_day": (total / unique / days) if unique else 0, "avg_time_user_week": (total / unique) if unique else 0}

    async def get_previous_week_stats(self, guild_id):
        now = datetime.now()
        end_last_week = int((now - timedelta(days=7)).timestamp() * 1000)
        start_last_week = int((now - timedelta(days=14)).timestamp() * 1000)
        query = "SELECT SUM(total_duration) as total FROM sessions WHERE guild_id = %s AND is_active = 0 AND start_time BETWEEN %s AND %s"
        r = await self._fetch(query, (str(guild_id), start_last_week, end_last_week), one=True)
        return r['total'] if r and r['total'] else 0

    async def get_sessions_on_date(self, guild_id, target_date):
        start_ts = int(datetime.combine(target_date, datetime.min.time()).timestamp() * 1000)
        end_ts = int(datetime.combine(target_date, datetime.max.time()).timestamp() * 1000)
        return await self._fetch("SELECT * FROM sessions WHERE guild_id = %s AND start_time < %s AND (end_time > %s OR is_active = 1)", (str(guild_id), end_ts, start_ts))

    async def start_session(self, user_id, guild_id, username):
        now_ts = int(datetime.now().timestamp() * 1000)
        now_human = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        row_id, _ = await self._execute("INSERT INTO sessions (user_id, guild_id, username, start_time, start_time_human, created_at) VALUES (%s, %s, %s, %s, %s, %s)", (user_id, guild_id, username, now_ts, now_human, now_ts))
        return row_id

    async def get_active_session(self, user_id, guild_id):
        return await self._fetch("SELECT * FROM sessions WHERE user_id = %s AND guild_id = %s AND is_active = 1 ORDER BY id DESC LIMIT 1", (user_id, guild_id), one=True)

    async def get_all_active_sessions(self, guild_id):
        return await self._fetch("SELECT * FROM sessions WHERE guild_id = %s AND is_active = 1 ORDER BY start_time DESC", (guild_id,))

    async def get_global_active_sessions(self):
        return await self._fetch("SELECT * FROM sessions WHERE is_active = 1")

    async def pause_session(self, user_id, guild_id):
        s = await self.get_active_session(user_id, guild_id)
        if not s or s['is_paused']: return False
        now = int(datetime.now().timestamp() * 1000)
        await self._execute("UPDATE sessions SET is_paused = 1, pause_start = %s WHERE id = %s", (now, s['id']))
        return True

    async def resume_session(self, user_id, guild_id):
        s = await self.get_active_session(user_id, guild_id)
        if not s or not s['is_paused']: return False
        now = int(datetime.now().timestamp() * 1000)
        dur = now - s['pause_start']
        await self._execute("UPDATE sessions SET is_paused = 0, pause_start = NULL, pause_duration = pause_duration + %s WHERE id = %s", (dur, s['id']))
        return True

    async def end_session(self, user_id, guild_id):
        s = await self.get_active_session(user_id, guild_id)
        if not s: return None
        now_ts = int(datetime.now().timestamp() * 1000)
        current_pause = (now_ts - s['pause_start']) if s['is_paused'] else 0
        total_pause = s['pause_duration'] + current_pause
        total_duration = now_ts - s['start_time'] - total_pause
        await self._execute("UPDATE sessions SET end_time = %s, end_time_human = %s, total_duration = %s, total_duration_human = %s, pause_duration = %s, pause_duration_human = %s, is_active = 0, is_paused = 0 WHERE id = %s", (now_ts, datetime.now().strftime('%d/%m/%Y %H:%M:%S'), total_duration, format_duration(total_duration), total_pause, format_duration(total_pause), s['id']))
        return {**s, 'total_duration': total_duration, 'pause_duration': total_pause, 'end_time': now_ts}

    async def add_time_adjustment(self, user_id, guild_id, username, ms):
        now_ts = int(datetime.now().timestamp() * 1000)
        await self._execute("INSERT INTO sessions (user_id, guild_id, username, start_time, start_time_human, end_time, end_time_human, total_duration, total_duration_human, is_active, is_paused, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, %s)", (user_id, guild_id, username, now_ts, datetime.now().strftime('%d/%m/%Y %H:%M:%S'), now_ts, datetime.now().strftime('%d/%m/%Y %H:%M:%S'), ms, format_duration(ms), now_ts))

    async def get_user_stats(self, user_id, guild_id):
        r = await self._fetch("SELECT username, COUNT(*) as total_sessions, SUM(total_duration) as total_time, AVG(total_duration) as avg_time, MAX(total_duration) as max_time, MIN(total_duration) as min_time, MIN(start_time) as first_service, MAX(start_time) as last_service FROM sessions WHERE user_id = %s AND guild_id = %s AND is_active = 0 GROUP BY user_id", (user_id, guild_id), one=True)
        stats = dict(r) if r else {'username': 'Inconnu', 'total_sessions': 0, 'total_time': 0, 'avg_time': 0, 'max_time': 0, 'min_time': 0, 'first_service': None, 'last_service': None}
        for k in ['total_time', 'avg_time', 'max_time', 'min_time']:
            if stats[k] is None: stats[k] = 0
        active = await self._fetch("SELECT start_time, pause_duration, is_paused, pause_start FROM sessions WHERE user_id = %s AND guild_id = %s AND is_active = 1", (user_id, guild_id), one=True)
        if active:
            now = int(datetime.now().timestamp() * 1000)
            if stats['last_service'] is None or active['start_time'] > stats['last_service']: stats['last_service'] = active['start_time']
            if stats['first_service'] is None: stats['first_service'] = active['start_time']
            current_session_time = active['pause_start'] - active['start_time'] - active['pause_duration'] if active['is_paused'] else now - active['start_time'] - active['pause_duration']
            if current_session_time > 0:
                stats['total_time'] += current_session_time
                stats['total_sessions'] += 1
                stats['avg_time'] = stats['total_time'] / stats['total_sessions']
                if current_session_time > stats['max_time']: stats['max_time'] = current_session_time
        return stats

    async def get_all_users_stats(self, guild_id):
        rows = await self._fetch("SELECT user_id, username, total_duration FROM sessions WHERE guild_id = %s AND is_active = 0", (guild_id,))
        active = await self._fetch("SELECT user_id, username, start_time, pause_duration, is_paused, pause_start FROM sessions WHERE guild_id = %s AND is_active = 1", (guild_id,))
        user_stats = {}
        for r in rows:
            uid = r['user_id']
            if uid not in user_stats: user_stats[uid] = {'username': r['username'], 'total_sessions': 0, 'total_time': 0}
            user_stats[uid]['total_sessions'] += 1
            user_stats[uid]['total_time'] += (r['total_duration'] or 0)
        now = int(datetime.now().timestamp()*1000)
        for r in active:
            uid = r['user_id']
            if uid not in user_stats: user_stats[uid] = {'username': r['username'], 'total_sessions': 0, 'total_time': 0}
            cur_time = (r['pause_start'] - r['start_time'] - r['pause_duration']) if r['is_paused'] else (now - r['start_time'] - r['pause_duration'])
            user_stats[uid]['total_time'] += cur_time
        res = [{'user_id': u, 'username': d['username'], 'total_sessions': d['total_sessions'], 'total_time': d['total_time']} for u, d in user_stats.items()]
        return sorted(res, key=lambda x: x['total_time'], reverse=True)

    async def get_user_date_range(self, user_id, guild_id):
        return await self._fetch("SELECT MIN(start_time) as first, MAX(start_time) as last FROM sessions WHERE user_id = %s AND guild_id = %s AND is_active = 0", (user_id, guild_id), one=True)

    async def get_all_user_sessions(self, user_id, guild_id):
        return await self._fetch("SELECT * FROM sessions WHERE user_id = %s AND guild_id = %s AND is_active = 0 ORDER BY start_time DESC", (user_id, guild_id))

    async def get_total_active_sessions_count(self):
        r = await self._fetch("SELECT COUNT(*) as cnt FROM sessions WHERE is_active = 1", one=True)
        return r['cnt'] if r else 0

    async def reset_guild_data(self, guild_id, time_window_ms=None):
        if time_window_ms:
            limit = int(datetime.now().timestamp() * 1000) - time_window_ms
            _, count = await self._execute("DELETE FROM sessions WHERE guild_id = %s AND start_time >= %s", (guild_id, limit))
        else:
            _, count = await self._execute("DELETE FROM sessions WHERE guild_id = %s", (guild_id,))
        return count

    async def cancel_active_session(self, session_id):
        _, count = await self._execute(
            "DELETE FROM sessions WHERE id = %s AND is_active = 1", (int(session_id),)
        )
        return count

    async def delete_user_data(self, guild_id, user_id):
        _, count = await self._execute("DELETE FROM sessions WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
        return count

    async def set_guild_config(self, guild_id, channel_id, message_id, log_channel_id=None, language='fr', direction_role_id=None, min_hours_goal=0, auto_roles_list=None, citizen_role_id=None, service_role_id=None, embed_color=None):
        self._config_cache.pop(str(guild_id), None)
        now_ts = int(datetime.now().timestamp())
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        await self._execute("INSERT INTO guild_config (guild_id, channel_id, message_id, log_channel_id, language, direction_role_id, min_hours_goal, auto_roles_list, citizen_role_id, service_role_id, embed_color, updated_at, updated_at_human) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE channel_id=VALUES(channel_id), message_id=VALUES(message_id), log_channel_id=VALUES(log_channel_id), language=VALUES(language), direction_role_id=VALUES(direction_role_id), min_hours_goal=VALUES(min_hours_goal), auto_roles_list=VALUES(auto_roles_list), citizen_role_id=VALUES(citizen_role_id), service_role_id=VALUES(service_role_id), embed_color=VALUES(embed_color), updated_at=VALUES(updated_at), updated_at_human=VALUES(updated_at_human)", (guild_id, channel_id, message_id, log_channel_id, language, direction_role_id, min_hours_goal, auto_roles_list, citizen_role_id, service_role_id, embed_color, now_ts, now_str))

    async def set_maintenance(self, guild_id, active):
        self._config_cache.pop(str(guild_id), None)
        await self._execute("UPDATE guild_config SET is_maintenance = %s WHERE guild_id = %s", (1 if active else 0, str(guild_id)))

    async def set_global_maintenance(self, active):
        await self._execute(
            "INSERT INTO bot_state (state_key, state_value) VALUES ('global_maintenance', %s) "
            "ON DUPLICATE KEY UPDATE state_value = VALUES(state_value)",
            ('1' if active else '0',)
        )

    async def get_global_maintenance(self):
        row = await self._fetch(
            "SELECT state_value FROM bot_state WHERE state_key = 'global_maintenance'", one=True
        )
        return bool(row and row['state_value'] == '1')

    async def grant_manual_premium(self, guild_id, granted_by):
        await self._execute(
            "INSERT INTO manual_premium (guild_id, granted_by, granted_at) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE granted_by = VALUES(granted_by), granted_at = VALUES(granted_at)",
            (str(guild_id), str(granted_by), int(time.time()))
        )

    async def revoke_manual_premium(self, guild_id):
        _, count = await self._execute(
            "DELETE FROM manual_premium WHERE guild_id = %s", (str(guild_id),)
        )
        return bool(count)

    async def has_manual_premium(self, guild_id):
        row = await self._fetch(
            "SELECT 1 FROM manual_premium WHERE guild_id = %s", (str(guild_id),), one=True
        )
        return row is not None

    async def get_manual_premium_guild_ids(self):
        rows = await self._fetch("SELECT guild_id FROM manual_premium")
        return {int(row['guild_id']) for row in rows}

    async def get_guild_config(self, guild_id):
        cached = self._config_cache.get(str(guild_id))
        if cached and time.time() < cached['expires']:
            return cached['data']
        row = await self._fetch("SELECT * FROM guild_config WHERE guild_id = %s", (guild_id,), one=True)
        if row: 
            self._config_cache[str(guild_id)] = {'data': row, 'expires': time.time() + 300}
        return row

    async def get_all_guild_configs(self):
        return await self._fetch("SELECT * FROM guild_config")

    async def add_blacklist(self, user_id: str, username: str = "Inconnu"):
        await self._execute("INSERT IGNORE INTO blacklist (user_id, username) VALUES (%s, %s)", (user_id, username))

    async def remove_blacklist(self, user_id: str):
        await self._execute("DELETE FROM blacklist WHERE user_id = %s", (user_id,))

    async def is_blacklisted(self, user_id: str) -> bool:
        return await self._fetch("SELECT 1 FROM blacklist WHERE user_id = %s", (user_id,), one=True) is not None
