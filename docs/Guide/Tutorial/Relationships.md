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

/// note

The relationship `Album` -> `Music` is `1 -> N`, in this case we use `list['TargetClass']` as type hint.

///


/// tip

Source and Target parameters can receive a list too, this is useful when you have tables that need many keys to be linked, for example `album: 'Album' = Dl(source=['album_id', 'year'], target=['id', 'year'])`

///

### Run query

Now in our debugger we can see nested schemas


![strawberry relationship](/assets/relationship.png){ width="800" .center}