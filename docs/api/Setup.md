This module sets up and configures the database connections using SQLAlchemy, managing asynchronous
and synchronous sessions for executing SQL queries. It also facilitates access control through custom
permission checks for GraphQL operations.

Classes:
    Setup: Provides methods to configure database engines, execute queries, and manage authentication
    and authorization checks for GraphQL requests based on custom permissions.

Functions:
    execute_query: Executes SQL queries using either asynchronous or synchronous database sessions,
    depending on the configuration.
    setup: Configures the database engine(s) and sets default functions for permission checks and
    query filtering.
    get_auth: Generates a permission class for Strawberry GraphQL that performs custom authentication
    and authorization checks.

Details:
    - The Setup class uses class-level attributes and methods to manage the application's database
      configuration and to perform SQL operations.
    - Permissions for GraphQL operations are handled dynamically, with the ability to enforce custom
      logic defined at runtime.

::: Setup