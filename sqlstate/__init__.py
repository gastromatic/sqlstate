from contextlib import asynccontextmanager, contextmanager
from dataclasses import InitVar, dataclass
from types import SimpleNamespace
from typing import Optional

import aiopg.sa as aio
from pydantic import BaseModel, FilePath
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.url import URL


class SqlTlsConfig(BaseModel):
    serverCa: FilePath
    clientCert: FilePath
    clientKey: FilePath

    def to_connect_args(self):
        return {
            "sslmode": "verify-ca",
            "sslcert": self.clientCert,
            "sslkey": self.clientKey,
            "sslrootcert": self.serverCa,
        }


class SqlConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str
    tls: Optional[SqlTlsConfig]


@dataclass(frozen=True)
class SchemaContainer:
    """
    Convenient wrapper for `tables` and/or `sql.Table`,
    guaranteeing that we've reflected the database and all tables are available.
    Also reflects views.
    """

    engine: InitVar[Engine]
    name: str

    def __post_init__(self, engine):
        metadata = MetaData(schema=self.name)
        metadata.reflect(bind=engine, views=True)
        object.__setattr__(self, "_metadata", metadata)

    def __getattr__(self, name):
        return Table(name, self._metadata, schema=self.name, mustexist=True)


def _make_schema_namespace(engine, **schemas):
    return SimpleNamespace(
        **{name: SchemaContainer(engine, schema) for name, schema in schemas.items()}
    )


@dataclass(frozen=True)
class SqlConnection:
    """
    Wrap an sqlalchemy Connection with access to the metadata
    """

    connection: Connection
    s: SimpleNamespace

    def __init__(self, connection: Connection, **schemas):
        object.__setattr__(self, "connection", connection)
        object.__setattr__(self, "s", SimpleNamespace(**schemas))

    def __getattr__(self, name):
        return getattr(self.connection, name)


class SqlState:
    def __init__(self, engine: Engine, **schemas):
        self.engine = engine
        self.s = _make_schema_namespace(engine, **schemas)

    @contextmanager
    def connect(self, **kwargs):
        with self.engine.connect(**kwargs) as c:
            yield SqlConnection(c, **vars(self.s))


class AsyncSqlState:
    def __init__(self, engine: aio.Engine, schemas_namespace):
        self.engine = engine
        self.s = schemas_namespace

    @asynccontextmanager
    async def acquire(self, **kwargs):
        async with self.engine.acquire(**kwargs) as c:
            yield SqlConnection(c, **vars(self.s))


def sql_from_config(config: SqlConfig, **schemas) -> SqlState:
    """
    Use the SqlConfig object to create an `SqlState`
    """
    url_params = config.dict(exclude={"tls"})
    url = URL("postgresql", **url_params)
    connect_args = config.tls.to_connect_args() if config.tls else {}
    engine = create_engine(url, connect_args=connect_args)
    return SqlState(engine, **schemas)


@asynccontextmanager
async def asql_from_config(config: SqlConfig, **schemas):
    connect_args = config.tls.to_connect_args() if config.tls else {}
    async with aio.create_engine(
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        dbname=config.database,
        **connect_args,
    ) as engine:
        sql_state = sql_from_config(config, **schemas)
        yield AsyncSqlState(engine, sql_state.s)


@asynccontextmanager
async def asql_from_engine(engine: Engine, **schemas):
    async with aio.create_engine(
        host=engine.url.host,
        port=engine.url.port,
        user=engine.url.username,
        password=engine.url.password,
        dbname=engine.url.database,
    ) as aengine:
        sql_state = SqlState(engine, **schemas)
        yield AsyncSqlState(aengine, sql_state.s)
