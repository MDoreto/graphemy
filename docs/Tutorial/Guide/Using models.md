{% include "templates/instalation.md" %}

The most interesting feature of Graphemy is the generation of queries with multi-level filters automaticly based on sqlmodel classes. This tutorial shows you how to use Graphemy with its features.

## Database Connection

Now, lets create a `main.py` file where we will setup our db connection, in our example I will use a in-memory database.

```Python hl_lines="4 5 11-15"
# main.py
{!./examples/query/main.py[ln:1-14]!}

# More code here later 👇
```

<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples/query/main.py!}
```

</details>

## FastApi Server

Setup the fastapi server with a default query, passing the created engine as parameter.

```Python hl_lines="2 3 9 18-21 24-26"
# main.py
{!./examples/query/main.py[ln:1-25]!}

# More code here later 👇
```

<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples//main.py!}
```

</details>

## Creating Models

Now we need to create the models that will represent our DB tables, for now our classes will be declared exactly the same of SQLmodel, but importing MyModel.
Create a `models` folder in project's folder and a `bank.py` file inside it.

```Python hl_lines="7"
# models/bank.py
{!./examples/query/models/bank.py[ln:1-8]!}

```
I recommend to create one file for each table. Create another file called `account.py`

```Python hl_lines="7"
# models/account.py
{!./examples/query/models/account.py[ln:1-9]!}

```

For the last we need set the in graphemy the folder that will be used to store models, this can be done with a environment variable.

```bash
set GRAPHEMY_PATH="models"
```

## Seed Data

### Create Tables

You have many ways to seed data into database, in this tutorial we will create tables using a default SQLmodel function that can be called from MyModel, but as we are creating table.

```Python hl_lines="28"
# main.py
{!./examples/query/main.py[ln:1-27]!}

# More code here later 👇
```

<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples//main.py!}
```

</details>

### Insert Rows

Here we will insert just a one bank and account that will be retrive after in our api.

```Python hl_lines="30-33 35-38"
# main.py
{!./examples/query/main.py[ln:1-38]!}

# More code here later 👇
```

## Starting server

Finally we can start our fastapi server running `uvicorn main:app` and then access `localhost:8000/graphql` and we will see the graphql debugger with our default 'hello world' query and bank and account queries.

![strawberry using_models](/assets/using_models.png){ width="800" .center}