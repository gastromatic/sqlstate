# Sqlstate

Python class for convenient database reflections and sql operations,
based on [sqlalchemy](https://www.sqlalchemy.org/).

The sqlstate object reflects multiple existing database schemas and
make them conventiently accessible, eg. as sqlalchemy Table objects.

## Usage

Say we have a database with existing schema `data` which contains
a table `users`. We can create the sql_state with:

```
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
```
sqlstate.s.my_schema.users
```

Selects, inserts and so on can be created as usual, see the sqlalchemy
documentation for details.