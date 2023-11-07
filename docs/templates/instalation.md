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