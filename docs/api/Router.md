This module provides functionalities to integrate GraphQL operations within a FastAPI application,
leveraging Strawberry's GraphQLRouter and SQLAlchemy for ORM operations. It includes custom data loaders,
query and mutation setup, and permission checks to ensure secure and efficient data handling.


Details:
    - The GraphemyRouter class configures GraphQL queries and mutations automatically based on metadata
      from SQLModel classes and handles permissions and custom filters.
    - It sets up a context for each request that includes custom data loaders for handling database
      operations efficiently.
    - The router also processes GraphQL responses, formatting errors, and managing permissions based on
      user requests.


::: graphemy.router