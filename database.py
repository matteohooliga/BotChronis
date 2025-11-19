
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import config


class ChronosDatabase:
    def __init__(self, db_name: str = config.DATABASE_NAME):
        self.db_name = db_name
        self.conn = None
        self.initialize_database()

    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def initialize_database(self):
        """Initialiser les tables de la base de données"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Table des sessions de service
        cursor.execute("""
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

        # Table de configuration des serveurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT,
                message_id TEXT,
                allowed_roles TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                updated_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Index pour optimisation
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user 
            ON sessions(user_id, guild_id, is_active)
        """)

        conn.commit()

    # ===== GESTION DES SESSIONS =====

    def start_session(self, user_id: str, guild_id: str, username: str) -> int:
        """Démarrer une nouvelle session de service"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = int(datetime.now().timestamp() * 1000)  # Millisecondes
        
        cursor.execute("""
            INSERT INTO sessions (user_id, guild_id, username, start_time)
            VALUES (?, ?, ?, ?)
        """, (user_id, guild_id, username, now))
        
        conn.commit()
        return cursor.lastrowid

    def get_active_session(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer la session active d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE user_id = ? AND guild_id = ? AND is_active = 1
            ORDER BY id DESC LIMIT 1
        """, (user_id, guild_id))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_active_sessions(self, guild_id: str) -> List[Dict[str, Any]]:
        """Récupérer toutes les sessions actives d'un serveur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE guild_id = ? AND is_active = 1
            ORDER BY start_time DESC
        """, (guild_id,))
        
        return [dict(row) for row in cursor.fetchall()]

    def pause_session(self, user_id: str, guild_id: str) -> bool:
        """Mettre en pause une session"""
        session = self.get_active_session(user_id, guild_id)
        if not session or session['is_paused']:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = int(datetime.now().timestamp() * 1000)
        
        cursor.execute("""
            UPDATE sessions 
            SET is_paused = 1, pause_start = ?
            WHERE id = ?
        """, (now, session['id']))
        
        conn.commit()
        return True

    def resume_session(self, user_id: str, guild_id: str) -> bool:
        """Reprendre une session en pause"""
        session = self.get_active_session(user_id, guild_id)
        if not session or not session['is_paused']:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = int(datetime.now().timestamp() * 1000)
        pause_duration = now - session['pause_start']
        
        cursor.execute("""
            UPDATE sessions 
            SET is_paused = 0, 
                pause_start = NULL,
                pause_duration = pause_duration + ?
            WHERE id = ?
        """, (pause_duration, session['id']))
        
        conn.commit()
        return True

    def end_session(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        """Terminer une session de service"""
        session = self.get_active_session(user_id, guild_id)
        if not session:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = int(datetime.now().timestamp() * 1000)
        total_duration = now - session['start_time']
        
        # Si en pause, ajouter la durée de pause actuelle
        if session['is_paused'] and session['pause_start']:
            current_pause_duration = now - session['pause_start']
            total_duration -= (session['pause_duration'] + current_pause_duration)
            total_pause = session['pause_duration'] + current_pause_duration
        else:
            total_duration -= session['pause_duration']
            total_pause = session['pause_duration']

        cursor.execute("""
            UPDATE sessions 
            SET end_time = ?,
                total_duration = ?,
                pause_duration = ?,
                is_active = 0,
                is_paused = 0,
                pause_start = NULL
            WHERE id = ?
        """, (now, total_duration, total_pause, session['id']))
        
        conn.commit()
        
        return {
            **session,
            'total_duration': total_duration,
            'pause_duration': total_pause,
            'end_time': now
        }

    # ===== STATISTIQUES =====

    def get_user_stats(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        """Obtenir les statistiques d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
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
        """, (user_id, guild_id))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_users_stats(self, guild_id: str) -> List[Dict[str, Any]]:
        """Obtenir les statistiques de tous les utilisateurs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
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
        """, (guild_id,))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_user_sessions(self, user_id: str, guild_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtenir l'historique des sessions d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        """, (user_id, guild_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]

    # ===== CONFIGURATION DES SERVEURS =====

    def set_guild_config(self, guild_id: str, channel_id: str, message_id: str):
        """Définir la configuration d'un serveur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO guild_config (guild_id, channel_id, message_id, updated_at)
            VALUES (?, ?, ?, strftime('%s', 'now'))
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                message_id = excluded.message_id,
                updated_at = strftime('%s', 'now')
        """, (guild_id, channel_id, message_id))
        
        conn.commit()

    def get_guild_config(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Obtenir la configuration d'un serveur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM guild_config WHERE guild_id = ?
        """, (guild_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def set_allowed_roles(self, guild_id: str, roles: List[str]):
        """Définir les rôles autorisés"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE guild_config 
            SET allowed_roles = ?, updated_at = strftime('%s', 'now')
            WHERE guild_id = ?
        """, (json.dumps(roles), guild_id))
        
        conn.commit()

    # ===== UTILITAIRES =====

    def reset_guild_stats(self, guild_id: str) -> int:
        """Réinitialiser toutes les sessions d'un serveur (supprime toutes les lignes).

        Args:
            guild_id: ID du serveur Discord

        Returns:
            Nombre de sessions supprimées
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM sessions WHERE guild_id = ?",
            (guild_id,)
        )
        deleted = cursor.rowcount if cursor.rowcount is not None else 0
        conn.commit()
        return deleted

    def close(self):
        """Fermer la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.conn = None
