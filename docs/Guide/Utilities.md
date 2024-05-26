## Strawberry extra Fields

You can use all Features of strawberry to add computed fields or your custom dataloaders, you just need to create a Strawberry class inside Graphemy class.

```python hl_lines="5-8"

class User(Graphemy, table = True):
    first_name:str
    last_name:str

    class Strawberry:
        @strawberry.field
        def full_name (self):
            return '{self.first_name} {self.last_name}'
```

/// note

For more details about strawberry fields: [Strawberry](https://strawberry.rocks/docs/general/schema-basics).

///


## Auto Foreign Keys

Graphemy can create foreign keys to your database based on Data Loaders. In every relation to 1, the source field will be referenced to target field.

```python
router = GraphemyRouter(engine=engine, auto_foreign_keys=True)
```

For example:

```python hl_lines="6"
{!./examples/tutorial/relationship/models.py[ln:12-18]!}

```

In this case `course.teacher_id` will be referenced to `teacher.id`  (`Students` wont do nothing because is a to N relationship)

/// note

If tou want a behavior different of the chosed in `GraphemyRouter` for a specific `Dl`, you can set it. `teacher: 'Teacher' = Dl(source='teacher_id', target='id', foreign_key = False)`

///