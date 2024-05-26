<img src="https://graphemy.readthedocs.io/en/latest/assets/logo.png" width="200">

# GRAPHEMY
[![Documentation Status](https://readthedocs.org/projects/graphemy/badge/?version=latest)](https://graphemy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/MDoreto/graphemy/graph/badge.svg?token=GJDMVBA425)](https://codecov.io/gh/MDoreto/graphemy)
![CI](https://github.com/MDoreto/graphemy/actions/workflows/pipeline.yml/badge.svg)
<a href="https://pypi.org/project/graphemy" target="_blank">
    <img src="https://img.shields.io/pypi/v/graphemy?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

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

## Prerequisites

Before you begin using Graphemy, it is highly recommended that you have some prior knowledge of the essential libraries upon which this project is built. This will help you make the most of the features and carry out integrations more effectively. Please make sure you are familiar with the following libraries:

**FastAPI**: A modern framework for building fast web APIs with Python. If you are not already familiar with FastAPI, you can refer to the [FastAPI documentation](https://fastapi.tiangolo.com/).

**SQLModel**: An object-relational mapping (ORM) library for Python that simplifies and streamlines database interactions. To learn more about SQLModel, visit the [SQLModel documentation](https://sqlmodel.tiangolo.com/).

**Strawberry**: A Python library for declaratively creating GraphQL schemas. For in-depth information on using Strawberry, access the [Strawberry documentation](https://strawberry.rocks/).

Having a solid understanding of these libraries is crucial to making the most of Project Name and effortlessly creating GraphQL APIs.

## Create a Project

I recomend you use Poetry, but you can use the enviroment manager that you want. So if you are using poetry, start the project:

```bash
# Create poetry project
poetry new graphemy tutorial

# Start Environment 
poetry shell
```

You can also use the environment manager wanted, such as virtualenv

```bash
# Create a directory for tutorial
mkdir graphemy-tutorial

# Enter into that directory
cd graphemy

# Create virtual environment
python -m venv venv

#Start Environment
venv/Scripts/Activate
```

## Requirements

Now install Graphemy :) 
```bash
poetry add graphemy
```
Or using default python env with pip:

```bash
pip install graphemy
```