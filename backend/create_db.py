"""
Скрипт создания базы данных PostgreSQL.

Использование:
    python create_db.py           — прочитает настройки из .env
    python create_db.py --drop    — сначала удалит БД, потом создаст заново
"""
import sys
import os

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("[ERROR] psycopg2 не установлен. Запустите: pip install psycopg2-binary")
    sys.exit(1)

try:
    from decouple import config
except ImportError:
    print("[ERROR] python-decouple не установлен. Запустите: pip install python-decouple")
    sys.exit(1)

# При запуске скрипта из директории backend/ .env лежит рядом,
# но если запускается из другой директории — ищем явно.
_script_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_script_dir, ".env")
if not os.path.exists(_env_path):
    _env_path = os.path.join(_script_dir, ".env.example")
    print(f"[WARN] .env не найден, читаю из .env.example: {_env_path}")

from decouple import AutoConfig
_cfg = AutoConfig(search_path=_script_dir)

DB_NAME     = _cfg("DB_NAME",     default="auth_db")
DB_USER     = _cfg("DB_USER",     default="postgres")
DB_PASSWORD = _cfg("DB_PASSWORD", default="postgres")
DB_HOST     = _cfg("DB_HOST",     default="localhost")
DB_PORT     = _cfg("DB_PORT",     default="5432")

DROP_FIRST = "--drop" in sys.argv


def get_admin_conn():
    """Подключение к системной БД postgres (для CREATE/DROP DATABASE)."""
    return psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def db_exists(cursor, name: str) -> bool:
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (name,),
    )
    return cursor.fetchone() is not None


def main():
    print(f"Подключение к PostgreSQL: {DB_USER}@{DB_HOST}:{DB_PORT}")
    try:
        conn = get_admin_conn()
    except psycopg2.OperationalError as exc:
        print(f"[ERROR] Не удалось подключиться к PostgreSQL:\n  {exc}")
        print("Проверьте DB_USER, DB_PASSWORD, DB_HOST, DB_PORT в файле .env")
        sys.exit(1)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    if DROP_FIRST:
        if db_exists(cur, DB_NAME):
            cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = %s AND pid <> pg_backend_pid()"
                ),
                (DB_NAME,),
            )
            cur.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB_NAME)))
            print(f"[OK] База данных '{DB_NAME}' удалена.")
        else:
            print(f"[INFO] База данных '{DB_NAME}' не существовала, пропускаю удаление.")

    if db_exists(cur, DB_NAME):
        print(f"[INFO] База данных '{DB_NAME}' уже существует. Ничего не делаю.")
        print("       Используйте --drop для пересоздания.")
    else:
        cur.execute(
            sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(
                sql.Identifier(DB_NAME)
            )
        )
        print(f"[OK] База данных '{DB_NAME}' создана.")

    cur.close()
    conn.close()

    print()
    print("Следующий шаг:")
    print("    python manage.py migrate")
    print("    python manage.py seed_data")


if __name__ == "__main__":
    main()
