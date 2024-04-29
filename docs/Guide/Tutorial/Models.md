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
{!./examples/tutorial/main.py[ln:1-25]!}
```
<details>
<summary>👀 Full file preview</summary>

```Python
{!./examples/tutorial/main.py!}
```

</details>

Add some records to get in our api.

```Python
{!./examples/tutorial/main.py[ln:27-60]!}
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

![strawberry put_mutation](/assets/put_mutation.png){ width="800" .center}


/// note

Put mutation can receive a id or not, if receive an id this endpoint will search for some item with this id and update it, if you don't put an id or it dont found some item with the inputed id, it will create a new item.

///
