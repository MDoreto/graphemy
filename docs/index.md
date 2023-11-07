![project's logo](assets/logo.png){ width="300" .center}
# GRAPHEMY

A Python library for integrating SQLModel and Strawberry, providing a seamless GraphQL integration with FastAPI and advanced features for database interactions.


## Overview

The Graphemy is designed to simplify and streamline the integration of SQLModel and Strawberry in Python projects. This library allows you to create a single class model, which, once declared, automatically provides GraphQL queries via Strawberry. These queries can be easily integrated into a FastAPI backend. All generated routes include filters on all fields, including a custom date filter. Additionally, it facilitates the creation of mutations for data modification and deletion by simply setting a variable in the model. The library also handles table relationships efficiently using Strawberry's dataloaders, providing a significant performance boost. Moreover, it offers a pre-configured authentication setup, which can be configured with just two functions.

## Features

- Integration of SQLModel and Strawberry for GraphQL support.
- Automatic generation of GraphQL queries for FastAPI.
- Powerful filtering capabilities, including custom date filters.
- Effortless creation of mutations for data manipulation.
- Efficient handling of table relationships using Strawberry's dataloaders.
- Pre-configured authentication setup for easy configuration.

{% include "templates/instalation.md" %}