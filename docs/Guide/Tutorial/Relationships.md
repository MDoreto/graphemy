### Setting Relationships

Create a link between our two models is a very simple task with graphemy, we just need a Dl attribute where we put what fields in current table make the relationship with target table.

It works basicly like foreign keys in a convencional database.


```Python  hl_lines="11"
# models/music.py
{!./examples/tutorial/models/music.py!}
```

In this case the relationship `Music` -> `Album` will be done using field `album_id` of `Music` and field `id` of `Album`.

```Python  hl_lines="9"
# models/music.py
{!./examples/tutorial/models/album.py!}
```

The Relationship `Album` -> `Music` will be done using field `id` of `Album` and field `album_id` of `Music`.

