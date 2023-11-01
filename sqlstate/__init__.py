from contextlib import asynccontextmanager, contextmanager
from dataclasses import InitVar, dataclass
from types import SimpleNamespace
from typing import Optional, AsyncIterator

from pydantic import BaseModel, FilePath
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine


class SqlTlsConfig(BaseModel):
    serverCa: Optional[FilePath]
    clientCert: Optional[FilePath]
    clientKey: Optional[FilePath]
    sslmode: str = "verify-ca"

    def to_connect_args(self):
        connect_params = {"sslmode": self.sslmode}
        if self.clientCert is not None:
            connect_params["sslcert"] = self.clientCert
        if self.clientKey is not None:
            connect_params["sslkey"] = self.clientKey
        if self.serverCa is not None:
            connect_params["sslrootcert"] = self.serverCa
        return connect_params


class SqlConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str
    engine_args: dict = {}
    async_engine_args: dict = {}
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
    """Wrap a sqlalchemy Connection with access to the metadata"""

    connection: Connection
    s: SimpleNamespace

    def __init__(self, connection: Connection, **schemas):
        object.__setattr__(self, "connection", connection)
        object.__setattr__(self, "s", SimpleNamespace(**schemas))

    def __getattr__(self, name):
        return getattr(self.connection, name)


@dataclass(frozen=True)
class AsyncSqlConnection:
    """Wrap an async sqlalchemy AsyncConnection with access to the metadata"""

    connection: AsyncConnection
    s: SimpleNamespace

    def __init__(self, connection: AsyncConnection, **schemas):
        object.__setattr__(self, "connection", connection)
        object.__setattr__(self, "s", SimpleNamespace(**schemas))

    def __getattr__(self, name):
        return getattr(self.connection, name)


class SqlState:
    def __init__(self, engine: Engine, **schemas):
        self.engine = engine
        self.s = _make_schema_namespace(engine, **schemas)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.engine.dispose()

    @contextmanager
    def connect(self):
        with self.engine.connect() as c:
            yield SqlConnection(c, **vars(self.s))


class AsyncSqlState:
    def __init__(self, engine: AsyncEngine, schemas_namespace):
        self.engine = engine
        self.s = schemas_namespace

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.engine.dispose()

    @asynccontextmanager
    async def acquire(self):
        async with self.engine.connect() as c:
            yield AsyncSqlConnection(c, **vars(self.s))


def sql_from_config(
    config: SqlConfig,
    engine_args: Optional[dict] = None,
    **schemas
) -> SqlState:
    """
    Use the SqlConfig object to create an `SqlState`
    """
    engine_args = engine_args or {}
    url_params = config.dict(exclude={"tls", "engine_args", "async_engine_args"})
    url = URL.create("postgresql", **url_params)
    connect_args = config.tls.to_connect_args() if config.tls else {}
    engine = create_engine(
        url, **{**config.engine_args, **engine_args}, connect_args=connect_args
    )
    return SqlState(engine, **schemas)


@asynccontextmanager
async def asql_from_config(
    config: SqlConfig,
    engine_args: Optional[dict] = None,
    connect_args: Optional[dict] = None,
    **schemas,
) -> AsyncIterator[AsyncSqlState]:
    engine_args = engine_args or {}
    url_params = config.dict(exclude={"tls", "engine_args", "async_engine_args"})
    url = URL.create("postgresql+asyncpg", **url_params)
    _connect_args = {**(connect_args or {}), **(config.tls.to_connect_args() if config.tls else {})}
    engine = create_async_engine(
        url, **{**config.async_engine_args, **engine_args}, connect_args=_connect_args
    )
    sql_state = sql_from_config(config, **schemas)
    yield AsyncSqlState(engine, sql_state.s)


@asynccontextmanager
async def asql_from_engine(
    engine: Engine,
    engine_args: Optional[dict] = None,
    **schemas,
) -> AsyncIterator[AsyncSqlState]:
    engine_args = engine_args or {}
    aengine = create_async_engine(
        engine.url,
        **engine_args,
    )
    sql_state = SqlState(engine, **schemas)
    yield AsyncSqlState(aengine, sql_state.s)
