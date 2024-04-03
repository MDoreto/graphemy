{% include "templates/instalation.md" %}
## Let's Code

### File Structure

I like to use a folder to store all my model classes and write one class per file, in our tutorial we will have a `main.py` file and a `models` folder.

### Create  some models

First, create a class to represente a database table, in our tutorial I will use a file `music.py` for this class and enable put and delete mutations for it.

```Python  hl_lines="6-7"
# models/music.py
{!./examples/tutorial/models/music.py[ln:1-9]!}
```

Lets create another class for our albums.

```Python 
# models/album.py
{!./examples/tutorial/models/album.py[ln:1-7]!}
```

### Setting a server

Then, create a router based on this query and import it in a fastapi app.

```Python
{!./examples/tutorial/main.py[ln:1-22]!}
```
<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples/tutorial/main.py!}
```

</details>

Add some records to get in our api.

```Python
{!./examples/tutorial/main.py[ln:22-31]!}
```
<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples/tutorial/main.py!}
```

</details>

## Testing

### Start FastApi

Run `uvicorn main:app` in the project's folder and access `localhost:8000/graphql` in your browser to see the strawberry debugger server.

### Run Query

Now you have queries for both classes created, and there put and delete mutations for music model

![strawberry basic_query](/assets/basic_query.png){ width="800" .center}

Note that every query already have a filter option where you can filter results by every rows.

![strawberry query_filter](/assets/query_filter.png){ width="800" .center}

### Run Mutation

For models that has the mutations enableds graphemy create the respective mutations.

