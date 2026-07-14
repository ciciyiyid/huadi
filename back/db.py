from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

import pymysql
from pymysql.cursors import DictCursor

from config import config


@contextmanager
def get_conn():
    conn = pymysql.connect(
        host=config.mysql_host,
        port=config.mysql_port,
        user=config.mysql_user,
        password=config.mysql_password,
        database=config.mysql_database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_all(sql: str, params: Optional[Iterable[Any]] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def query_one(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def execute(sql: str, params: Optional[Iterable[Any]] = None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            return cursor.execute(sql, params)


def execute_many(sql: str, params_list: Iterable[Iterable[Any]]) -> int:
    with get_conn() as conn:
        with conn.cursor() as cursor:
            return cursor.executemany(sql, params_list)
