Graphemy router accepts some auxiliary functions that make possible do a complete access control in every levels of the api.

## permission_getter

In the most part of cases you will just need this method, because you can control access for each table using it.

### Generic use

If we will use same logic to define the control aceess for every table in our api we can declare a function that will receive params `parametros` and should return a boolen that indicate if this request has the needed permissions for the table.

### Specific use

If you want that some specifics tables have a specifics logic, you can declare a `permission_getter` function inside the class, then Graphemy will check if this function or the generic function (if exists) allow this request access this table.


### query_filter

### dl_filter

