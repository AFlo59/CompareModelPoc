"""
Module de base de données optimisé avec performance améliorée
"""

import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuration optimisée pour SQLite."""
    
    # Chemin de la base de données
    DB_PATH = Path("database.db")
    
    # Configuration SQLite pour les performances
    PRAGMA_SETTINGS = [
        "PRAGMA journal_mode=WAL",              # Write-Ahead Logging pour de meilleures performances
        "PRAGMA synchronous=NORMAL",            # Balance entre sécurité et performance  
        "PRAGMA cache_size=10000",              # Cache plus important (40MB)
        "PRAGMA temp_store=MEMORY",             # Tables temporaires en mémoire
        "PRAGMA mmap_size=268435456",           # Memory-mapped I/O (256MB)
        "PRAGMA optimize",                      # Optimisation automatique des statistiques
    ]
    
    # Version du schéma pour les migrations
    SCHEMA_VERSION = 4
def get_db_path() -> Path:
    """Retourne le chemin de la base, en honorant les surcharges de tests.
    Priorité à `DatabaseConfig.DB_PATH` (patchable dans les tests), sinon
    repli sur l'alias de module `DB_PATH`.
    """
    # 1) Priorité à la variable d'environnement (Docker/production)
    env_db = os.getenv("DATABASE_PATH")
    if env_db:
        return Path(env_db)

    module_db = None
    try:
        module_db = DB_PATH  # type: ignore[name-defined]
    except Exception:
        module_db = None
    config_db = None
    try:
        config_db = getattr(DatabaseConfig, "DB_PATH", None)
    except Exception:
        config_db = None

    # Si DatabaseConfig.DB_PATH est défini et différent de l'alias module, on le privilégie (cas de tests patchés)
    if config_db and (not module_db or str(config_db) != str(module_db)):
        return Path(config_db)
    # Sinon, on utilise l'alias module s'il est disponible (cas des fixtures qui patchent DB_PATH)
    if module_db:
        return Path(module_db)
    # Repli par défaut
    return Path("database.db")


class DatabaseConnection:
    """Gestionnaire de connexion optimisé avec pooling basique."""
    
    _thread_local = threading.local()
    
    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Retourne une connexion SQLite optimisée."""
        # Une connexion par thread pour éviter les conflits
        # Si une connexion existe mais est fermée/invalide, on la recrée.
        if hasattr(cls._thread_local, 'connection'):
            try:
                # Vérifie que la connexion est valide
                cls._thread_local.connection.execute("SELECT 1")
            except sqlite3.Error:
                try:
                    cls._thread_local.connection.close()
                except Exception:
                    pass
                del cls._thread_local.connection
        if not hasattr(cls._thread_local, 'connection'):
            cls._thread_local.connection = cls._create_optimized_connection()
        
        return cls._thread_local.connection
    
    @classmethod
    def _create_optimized_connection(cls) -> sqlite3.Connection:
        """Crée une connexion SQLite avec optimisations."""
        # Utiliser un getter patch-friendly pour compatibilité avec les tests
        conn = sqlite3.connect(
            get_db_path(),
            check_same_thread=False,
            timeout=30.0,  # Timeout de 30 secondes
            isolation_level=None  # Autocommit mode
        )
        
        # Activer les clés étrangères
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Appliquer les optimisations SQLite
        for pragma in DatabaseConfig.PRAGMA_SETTINGS:
            try:
                conn.execute(pragma)
                logger.debug(f"Appliqué: {pragma}")
            except sqlite3.Error as e:
                logger.warning(f"Échec {pragma}: {e}")
        
        # Factory pour row objects
        conn.row_factory = sqlite3.Row
        
        logger.debug("Connexion SQLite optimisée créée")
        return conn
    
    @classmethod
    def close_all_connections(cls):
        """Ferme toutes les connexions ouvertes."""
        if hasattr(cls._thread_local, 'connection'):
            cls._thread_local.connection.close()
            del cls._thread_local.connection

class DatabaseSchema:
    """Gestionnaire de schéma avec migrations versionnées."""
    
    @staticmethod
    def get_schema_version(conn: sqlite3.Connection) -> int:
        """Récupère la version actuelle du schéma."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_info LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.OperationalError:
            return 0
    
    @staticmethod
    def set_schema_version(conn: sqlite3.Connection, version: int):
        """Met à jour la version du schéma."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_info (
                version INTEGER PRIMARY KEY
            )
        """)
        cursor.execute("DELETE FROM schema_info")
        cursor.execute("INSERT INTO schema_info (version) VALUES (?)", (version,))
        conn.commit()
    
    @classmethod
    def create_tables(cls, conn: sqlite3.Connection):
        """Crée toutes les tables avec index optimisés."""
        cursor = conn.cursor()
        
        # Table utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Index pour les utilisateurs
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)")
        
        # Table choix de modèles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_model_choices_user ON model_choices(user_id)")
        
        # Table campagnes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                themes TEXT,
                language TEXT NOT NULL,
                ai_model TEXT DEFAULT 'GPT-4o',
                gm_portrait TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour les campagnes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_active ON campaigns(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_updated ON campaigns(updated_at)")
        
        # Table personnages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                name TEXT NOT NULL,
                class TEXT,
                race TEXT,
                gender TEXT,
                level INTEGER DEFAULT 1,
                description TEXT,
                portrait_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
            )
        """)
        
        # Index pour les personnages
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_user ON characters(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_campaign ON characters(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_active ON characters(is_active)")
        
        # Table messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant')),
                content TEXT NOT NULL,
                character_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE SET NULL
            )
        """)
        
        # Index pour les messages (critiques pour la performance)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_campaign ON messages(campaign_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role)")
        
        # Table performance logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                campaign_id INTEGER,
                model TEXT NOT NULL,
                latency REAL NOT NULL,
                tokens_in INTEGER NOT NULL,
                tokens_out INTEGER NOT NULL,
                cost_estimate REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour les performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_user ON performance_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_model ON performance_logs(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_campaign ON performance_logs(campaign_id)")
        
        logger.info("Toutes les tables et index créés avec succès")
    
    @classmethod
    def run_migrations(cls, conn: sqlite3.Connection):
        """Exécute les migrations nécessaires."""
        current_version = cls.get_schema_version(conn)
        
        if current_version < 1:
            logger.info("Migration vers version 1: Ajout de colonnes timestamps")
            cls._migration_v1(conn)
        
        if current_version < 2:
            logger.info("Migration vers version 2: Optimisation des index")  
            cls._migration_v2(conn)
        
        if current_version < 3:
            logger.info("Migration vers version 3: Ajout contraintes et colonnes")
            cls._migration_v3(conn)
        
        if current_version < 4:
            logger.info("Migration vers version 4: Ajout de la colonne ai_model sur campaigns")
            cls._migration_v4(conn)
        
        # Mettre à jour la version finale
        if current_version < DatabaseConfig.SCHEMA_VERSION:
            cls.set_schema_version(conn, DatabaseConfig.SCHEMA_VERSION)
            logger.info(f"Base de données migrée vers la version {DatabaseConfig.SCHEMA_VERSION}")
    
    @staticmethod
    def _migration_v1(conn: sqlite3.Connection):
        """Migration version 1."""
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE campaigns ADD COLUMN gm_portrait TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN campaign_id INTEGER")
        except sqlite3.OperationalError:
            pass
    
    @staticmethod
    def _migration_v2(conn: sqlite3.Connection):
        """Migration version 2."""
        cursor = conn.cursor()
        
        # Ajouter les nouveaux index si ils n'existent pas
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_campaign_timestamp ON messages(campaign_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_performance_user_model ON performance_logs(user_id, model)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError:
                pass
    
    @staticmethod  
    def _migration_v3(conn: sqlite3.Connection):
        """Migration version 3."""
        cursor = conn.cursor()
        
        # Ajouter nouvelles colonnes
        new_columns = [
            ("users", "last_login", "DATETIME"),
            ("users", "is_active", "BOOLEAN DEFAULT 1"),
            ("campaigns", "updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("campaigns", "is_active", "BOOLEAN DEFAULT 1"),
            ("characters", "gender", "TEXT"),
            ("characters", "is_active", "BOOLEAN DEFAULT 1"),
            ("performance_logs", "cost_estimate", "REAL"),
        ]
        
        for table, column, definition in new_columns:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError:
                pass

    @staticmethod
    def _table_has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
        """Retourne True si la colonne existe dans la table. Tolère les mocks dans les tests."""
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            rows = cursor.fetchall()
            if not rows:
                return False
            column_names = []
            for row in rows:
                # sqlite3.Row or tuple: second element is the column name
                try:
                    name = row[1]
                except Exception:
                    try:
                        name = row.get("name")  # type: ignore[attr-defined]
                    except Exception:
                        name = None
                if name:
                    column_names.append(name)
            return column_name in column_names
        except Exception:
            # En cas de mock incomplet dans les tests, retourner False pour tenter l'ALTER TABLE
            return False

    @staticmethod
    def _migration_v4(conn: sqlite3.Connection):
        """Migration version 4: ajoute la colonne ai_model à campaigns si manquante."""
        try:
            if not DatabaseSchema._table_has_column(conn, "campaigns", "ai_model"):
                cursor = conn.cursor()
                cursor.execute("ALTER TABLE campaigns ADD COLUMN ai_model TEXT DEFAULT 'GPT-4o'")
                conn.commit()
        except sqlite3.OperationalError:
            # Si la table n'existe pas encore, elle sera créée par create_tables
            pass

@contextmanager
def get_optimized_connection():
    """Context manager pour connexions optimisées avec gestion d'erreurs."""
    conn = None
    try:
        conn = DatabaseConnection.get_connection()
        try:
            conn.execute("BEGIN")
        except sqlite3.Error:
            # Si la connexion est invalide/fermée, on la recrée et on recommence
            DatabaseConnection.close_all_connections()
            conn = DatabaseConnection.get_connection()
            conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception as rb_err:
                logger.error(f"Échec du rollback (connexion invalide ?): {rb_err}")
        logger.error(f"Erreur base de données, rollback tenté: {e}")
        raise

def init_optimized_db():
    """Initialise la base de données avec optimisations."""
    logger.info("Initialisation de la base de données optimisée")
    
    # Créer le répertoire si nécessaire avec gestion d'erreurs/permissions
    db_dir = get_db_path().parent
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Impossible de créer le répertoire DB {db_dir}: {e}")
        raise
    
    with get_optimized_connection() as conn:
        # Créer les tables
        DatabaseSchema.create_tables(conn)
        
        # Exécuter les migrations
        DatabaseSchema.run_migrations(conn)
        
        # Optimiser la base de données
        conn.execute("ANALYZE")
        conn.execute("PRAGMA optimize")
        
    logger.info("Base de données optimisée initialisée avec succès")

def get_connection() -> sqlite3.Connection:
    """Fonction de compatibilité pour l'ancienne API."""
    return DatabaseConnection.get_connection()

# Fonction d'initialisation principale (rétrocompatibilité)
def init_db():
    """Initialise la base de données (interface de compatibilité)."""
    init_optimized_db()

# Alias pour rétrocompatibilité avec les tests
DB_PATH = DatabaseConfig.DB_PATH