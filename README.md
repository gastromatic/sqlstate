# Sqlstate

Python class for convenient database reflections and sql operations,
based on [sqlalchemy](https://www.sqlalchemy.org/).

The sqlstate object reflects multiple existing database schemas and
make them conventiently accessible, eg. as sqlalchemy Table objects.

The sqlstate is intented to be useful in combination with the 
sqlalchemy core, without using the sqlalchemy ORM.

## Usage

Say we have a database with existing schema `data` which contains
a table `users`. We can create the sql_state with:

```python
from sqlstate import SqlConfig, sql_from_config

config = {
    "host": "localhost"
    "port": 5433
    "database": "my_database"
    "username": "postgres"
    "password": "postgres"
}
sqlstate = sql_from_config(
        SqlConfig(**config), my_schema="data",
    )
```

The line `my_schema="data"` reflects the schema `data` and makes
it accessible as `sqlstate.s.my_schema`. It is possible to reflect
multiple schemas in this way by adding further keyword arguments.

The sqlalchemy Table object for the `users` table is accessible as
```python
sqlstate.s.my_schema.users
```

Selects, inserts and so on can be created as usual, see the sqlalchemy
documentation for details.

## Engine and connections

The engine can be selected with `sql_state.engine`. A connection
can be aquired by `sql_state.acquire()`.

## Usage in async programming

There is also an `AsyncSqlState` and a function `asql_from_config`,
which create an async sqlstate. A connection aquired from this state
can eg. be used as follows:
```python
async with sql_state.acquire() as conn:
    await conn.execute(some_query)
```
