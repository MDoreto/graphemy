Graphemy router accepts some auxiliary functions that make possible do a complete access control in every levels of the api.



## Table Control


In the most part of cases you will just need this method, because you want control access for each table using it.

### permission_getter

If we will use same logic to define the control aceess for every table in our api we can declare a function that will receive the class of the query (`Graphemy` model that you declared to represent the table that is been used), context of request and query type( string with the type of request: 'query', 'put_mutation', 'delete_mutation') and should return a boolen that indicate if this request has the needed permissions for the table.

``` python
{!./examples/tutorial/auth/main.py[ln:37-39]!}

{!./examples/tutorial/auth/main.py[ln:60-61]!}
```

/// note

These Functions and the following functions should be passed to `GraphemyRouter`.

``` python
{!./examples/tutorial/auth/main.py[ln:65-71]!}
```

for more details about context:[Strawberry](https://strawberry.rocks/docs/integrations/fastapi#context_getter).

///

/// tip

You can also set a `permission_getter` function inside a `Graphemy` class to make this control more specific to each table.

If you set a generic `permission_getter` in router and also in a model, the model `permission_getter` has priority above router's `permission_getter`

///

## Rows Control

Its a more complex access control, lets supose that some user can get data from some table, but just lines that has value 'A' in column 'category', in this case we need use two auxiliary functions that will be passed to `GraphemyRouter`:

### query_filter

This function responsible to put a filter inside all main querys, using our example, we will have something like:

``` python
{!./examples/tutorial/auth/main.py[ln:37-39]!}

{!./examples/tutorial/auth/main.py[ln:54-57]!}
```

/// note

This function should return a SQLAlchemy filter statement.

///

### dl_filter


This function responsible to put a filter inside all main querys, using our example, we will have something like:

``` python
{!./examples/tutorial/auth/main.py[ln:37-39]!}

{!./examples/tutorial/auth/main.py[ln:42-51]!}
```

/// note

This function receive data returned from querie and should return data filtered.

///