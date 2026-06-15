"""
DECEPTR API — Connexions partagées Elasticsearch + MySQL
Utilisé par tous les routers FastAPI.
"""
import aiomysql
from elasticsearch import AsyncElasticsearch
from config import (
    ELASTIC_HOST, ELASTIC_USER, ELASTIC_PASSWORD, EVENTS_INDEX,
    MYSQL_HOST, MYSQL_DB, MYSQL_USER, MYSQL_PASSWORD
)

_es_client = None
_mysql_pool = None


def get_es() -> AsyncElasticsearch:
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            hosts=[ELASTIC_HOST],
            basic_auth=(ELASTIC_USER, ELASTIC_PASSWORD),
            verify_certs=False,
        )
    return _es_client


async def get_mysql_pool() -> aiomysql.Pool:
    global _mysql_pool
    if _mysql_pool is None:
        _mysql_pool = await aiomysql.create_pool(
            host=MYSQL_HOST, db=MYSQL_DB,
            user=MYSQL_USER, password=MYSQL_PASSWORD,
            minsize=1, maxsize=10, autocommit=True, connect_timeout=10
        )
    return _mysql_pool


EVENT_INDEX_PATTERN = f"{EVENTS_INDEX}-*"
