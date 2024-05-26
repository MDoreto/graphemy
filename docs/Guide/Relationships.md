### Setting Relationships

Create a link between our two models is a very simple task with graphemy, we just need a Dl attribute where we put what fields in current table make the relationship with target table.

It works basicly like foreign keys in a convencional database.


```Python  hl_lines="10 18"
# models.py
{!./examples/tutorial/relationship/models.py[ln:1-18]!}
```

In this case the relationship `Teacher` -> `Course` will be done using field `teacher_id` of `Course` and field `id` of `Teacher`.


/// note

As the relationship `Teacher` -> `Course` is `1 -> N`, in this case we use `list['TargetClass']` as type hint.

///


Source and Target parameters can receive a list too, this is useful when you have tables that need many keys to be linked, for example:

```Python  hl_lines="8-10 18-20"
# models.py
{!./examples/tutorial/relationship/models.py[ln:26-45]!}
```


/// tip

If you want use a static string or number to make the link between two models, you can pass the string with `_` prefix or the number in `source` and `target`. Ex: `some_field: 'SomeClass' = Dl(source=['some_field', 12, '_staticstring'], target=['target_field', 'month', 'category'])`

Here graphemy will search a row of `SomeClass` that has:

 `source_table.some_field` == `target_table.target_field` 

 `target_table.month == 12` 

 `target_table.category == 'staticstring'` 

///

### Run query

Now in our debugger we can see nested schemas


![strawberry relationship](/assets/relationship.png){ width="800" .center}

/// tip

Nested fileds also have filters that can be used individually same the main query filters.

///