# CmdApp

I like the "declarative style" of code. So in this project, you can create a Command Line Application just focusing on the logic of the commands.

## Basic Guide

First, if your project interacts with a database, you can create a `database.Database` object with a schema.

A database schema is just a dict whose keys are the table names and whose values ​​are dicts describing the table - a [Table Metadata](#table-metadata).

Next, you should define one or more `core.Prototype` subclasses that contain static methods that define the logic for each command your application supports.

You can organize commands into multiple `Prototype` subclasses, each containing a group of related commands.

A prototype method to become a command must be named in the format `do_<name>` (following the cmd2 convention) and decorated with `core.as_command()`. The `as_command` decorator describes the data used to convert prototypes into actual commands. You should check [Command Metadata](#command-metadata) for details.

The parameters of the prototype method are similar to the cmd2 application's command method. They are:

- An instance of `CmdApp` (inherited from `cmd2.Cmd`) containing the generated commands.
- An instance of [`argparser.Namespace`](https://docs.python.org/3/library/argparse.html#argparse.Namespace) instance containing command arguments parsed from user input.
- List of arguments that are not predefined (a.k.a unknown, ...). Available only if command metadata is declared with `custom = True`.
- One or more keyword arguments (you can call them as contextual arguments) if command metadata is declared with `dependencies`. See [Contextual Command](#contextual-command)

Finally, with the `Database` (if your app needs it) and `Prototype` instances, you can pass them to `core.start_app()` to create and run the app.

`start_app` is a helper function that does simple work to wire up all the pieces an application needs: **Application Class** (to create an application instance), **Application Prototype** (to contain command logic), and **Database** (optionally, to contain database logic).

You can write a better function for your project but still keep the core logic of `start_app` in your custom function:

- Apply the prototype instances to the application class (using `Prototype.apply_to`). It will return the created commands in their respective categories.
- Then, instantiate the application class and set the command category to the result from the previous step.
- Call `app.cmdloop()` to start the command loop that accepts user input and processes it.
- Finally, you should call `app.terminate()` to clean up the application (like closing the database connection).

As flexible as other features, you can also derive from App Class (`core.CmdApp`). In this project, I also created `BasePrototype` and `BaseApp` classes which support basic operations on Database like CRUDL and Exporting data to files in different formats (CSV, JSON, YAML).

You can see the examples in [this](./cmdapp/example/) to better understand the above flows.

## Features

Most of the objects in this application can be created through declarations, which are called metadata.

### Field Metadata

Field Metadata is a common representation between Database Column and Command Arguments. In fact, there are many commands whose arguments are data fields in the database. Therefore, I aim to have a common metadata class for them.

#### Field Attributes

A Field Metadata (`parser.FieldMeta`) includes data type (`dtype`), default value (`default`), not null directive (`required`), description (`comment`), list of possible values ​​(`choices`), how to process data (`proc`) and some supporting fields for argparser such as `action`, `nargs`, `metavar`, `flags` (not all argparser options can be used).

About `dtype`, it is a unified data type that can serve 3 functions: Handling user data (text, as command line input), Processing in Python and storing in SQLite database.

For example, with date-time data, you can declare `dtype = "datetime"`. Then, users can enter date format strings such as `now`, `-3.days`, `20241212203045`,... it will be processed into `datetime` type in Python and will be stored in the database in ISO format.

Some `dtypes` that the application supports: Check the variable `types.SUPPORT_DTYPES`.

About `proc`, it is used to process user input data or process complex data like parsing item from an `array`.

For example, with text, to support inputting Vietnamese data right on the command line interface, you can declare `proc = "telex"`. Then, if the user enters `Xin chaof Vieejt Nam`, the data stored in the database can be `Xin chào Việt Nam` (if your terminal can display unicode, you can see it)

Note that: `dtype` and `proc` do not support customization yet. They are all fixed with predefined values.

#### Declare a FieldMeta

You can declare a `FieldMeta` via a dict (with key is above attributes) or a string.

##### Annotation

With strings, I call the syntax Annotation, which is quite similar to Python's annotation syntax but a bit more extensive. The annotation string will be parsed as dict onward.

Annotation syntax is made up of 3 optional parts, in following order:

**Flags**: (Used by argparser, assigned to `flags`) Declare additional flags for the field. Flags are separated by commas (,) and do not have a `-` or `--` prefix (they are added by default). You can use `*` to indicate that this field is a **positional argument** (see argparser for details).

Notes that the field name always is a flag.

**Datatype**: Description of the field's data-related properties including `required`, `dtype`, `proc`, `choices` and `default`.

The datatype part needs to be enclosed in **parentheses** (it can also contain parentheses inside) and has following syntax:

```
(<* if required><dtype>[<proc>]: [<choices>] = <default>)
```

Notes that, `[`, `]`, `:`, `=` are literals used to separated subparts. **The `dtype` subpart is required**. You can check the Regex syntax of it by `parser.annotation.ANNOTATION_DATATYPE_PATTERN`.

The `<choices>` item value must be a JSON string (e.g. a quote for text) but `<default>` is not always (just in some cases). That's because `<choices>` is an array and it is parsed as JSON but `<default>` depends on `dtype`.

**Comment**: This part describes the field, which will be used as part of the help message for the corresponding argparser argument. It should be appended with a colon (:). **The colon is required even if the other parts are not declared**.

Example:

```python
"w, hello (*array[int]: [[1, 2], [2, 3], [3, 1]] = [1, 2]): set width scale to the column"

# dict(
#     flags=["w", "hello"],
#     comment="set width scale to the column",
#     dtype="array",
#     proc="int",
#     required=True,
#     choices=[[1, 2], [2, 3], [3, 1]],
#     default=[1, 2],
# ),
```

##### Override a defined FieldMeta

The annotation syntax is best for common uses, but in some cases you should use dict to override some attributes for `FieldMeta` or to assign values ​​to some other attributes (which Annotation cannot interpret).

You can combine both annotation and dict syntax to declare a `FieldMeta` by assigning annotation to the `annotation` item of the dict. But the other items on the dict will override any attributes parsed by the annotation.

Note that some attributes can be implicitly assigned (when parsed as argparser argument) based on other attributes. For example, when you declare `dtype = "array"`, by default, `nargs` will be `*`, or when `dtype = "bool", default = False` then `action = "store_true"`.

### Table Metadata

Table Metadata contains descriptive data for the Database Table, including: columns (`FieldMeta`), metadata columns (columns like timestamp columns) and constraints (UNIQUE, CHECK,...) at the Table level.

#### Attributes and Declare

Table Metadatas are usually defined in Database Schema and parsed on creating a `database.Database` instance.

`TableMeta` includes the following attributes:

- `columns`: Mapping from name to `FieldMeta`s of the table columns. You can use annotation or dict syntax to declare `FieldMeta`s.
- `meta-columns`: Names of meta columns used by the table. Currently, the project only defines 3 meta columns corresponding to timestamps for `created_at`, `updated_at` and `deleted_at`.
  - The ID column is considered a meta column, but it is predefined and cannot be overridden.
- `constraints`: List of constraints of the Table, constraints are strings in SQLite syntax.
- `singular`: Table name in singular form, for display purposes, default to the table name.
- `plural`: Table name in plural form, for display purposes.

### Command Metadata

Prototype is a logical blueprint to generate commands for the application. So it needs some data to be a actual command (that able to interact with the user). That data is called Command Metadata.

With command metadata, the application can convert the prototype into commands that have not only logic but also arguments. So command metadata is a declarative way of how to process user input. From there, it is possible to create arguments and pass them to the prototype method.

#### Command Attributes

In most cases, you do not need to work directly with the `CommandMeta` object. Instead, use the `as_command` decorator to decorate a prototype method. The arguments to these decorators are metadata for the command, including:

- `description` and `epilog`: Describe the functionality of the command. They are used to display on the Help message of the created command. Similar to the `description` and `epilog` of an argparser object.
- `category`: Category to group many commands (on listing with `help -v`). If not specified, the name of the `Prototype` class will be used.
- `custom`: Set True when you want the command to accept arguments that have not been declared. This list of arguments will be passed to the Prototype function as a list. Similar to cmd2's `with_unknown_args`
- `arguments`: Mapping from name to `FieldMeta`s of the command arguments. You can use annotation or dict syntax to declare `FieldMeta`s.
- `dependencies`: Declare context dependencies for the prototype. See [Contextual Command](#contextual-command)

#### Contextual Command

In fact, one prototype method can be used to generate multiple commands for the application. This happens when multiple commands have the same logic, they only differ in the input arguments. I call this type of commands is contextual commands. From the prototype's view, the commands are in different contexts. And the prototype, to be a real command needs to be placed in a specific context. So, the prototype depends on some contexts.

A prototype's dependencies are declared with additional keyword parameters in its declaration. The name of the parameters are the **context types** and their values are **context objects**, which will be populated during command generation.

The context objects for generated commands are declared in `CommandMeta` with `dependencies` attribute, as expected.The `dependencies` attribute expect a dict for its value, with following keys:

- `type`: The context type that the prototype depends on. It must be same as prototype extra keyword parameter.
- `values`: The key is to retrieve a single context from a set of context objects that the prototype depends on. Sometimes, you cannot pre-define context objects at declaration time. So, use get keys instead of real contexts is a choice of design.
- `arguments`: In different contexts, command arguments are often different. So this option allows you to add additional arguments (in addition to the `CommandMeta`'s predefined `arguments`) for the specific context object. The value for this option is a function that has one parameter and is expected to return a dict of arguments metadata.
- `parser`: Along with arguments, other command metadata such as `description` or `epilog` or argument help messages will also change depending on the context. This option helps parse the text value into a more context-specific version. The value for this option is a function with 2 parameters, respectively the value to parse and the context object, and of course it should return the parsed version of the input value.

#### How it works

When you are done declaring your prototype methods and their metadata with the `as_command` decorator, you should call `apply_to` on the `Prototype` subclass instance to assign all declared prototypes to one Application class (e.g. `CmdApp`). `apply_to` will filter out which methods are prototypes, then depending on the corresponding `CommandMeta` object, it converts each prototype into one or more command methods (just like the `cmd2` command method), and assign them all to the application class (so `cmd2` can recognize them).

The most important question is **what's inside the prototype-to-command conversion?**

As you know, there are 2 types of prototypes, one that is context dependent and one that is context independent.

For a context-independent prototype, the command metadata will first be called to parse its internal data into a `Cmd2ArgumentParser`, then use `with_argument_parser` to decorate the prototype to make a command method. That is!

For the context-dependent one, the first process is to retrieve the context on which the prototype depends. Then, based on each context object retrieved, it generates new context-specific arguments along with the context-specific help message. From this point on, the process is the same as the normal case above.

But it should be noted that for each context we are creating a new command, so the number of commands can be very large and diluted. Therefore, as a choice of design, there is always a context-dependent command (called a **placeholder command**) created along with the context-dependent commands. The role of the placeholder command is to introduce context-derived commands when **these derived commands are hidden**.

The placeholder command has only one argument - the value of the context key - which determines the derived command that will be called for execution. Instead of calling a command directly, the user can call it through a placeholder command.

But, **how does a context-dependent prototype get a context object?**

As noted above, sometimes you cannot determine the context object at declaration time. Therefore, the context objects must be defined and passed into the `Prototype` constructor. You should pass a **context store** into the constructor, mapping from the _context type_ to the _context collection_. A _context collection_ is a mapping of _context keys_ and _context objects_. With this design, a `Prototype` class can have multiple prototype methods and each method uses a different collection of contexts. From the context collection and context keys predefined in `CommandMeta`, the context objects for the prototype method are determined.

### Response

`Response` is a helper class that allows applications to respond to users in a variety of presentation formats.

In current version, I defined 3 types of `Response` format:

**Response a `message`**: Response with a message. To have a common structure for messages, messages should follow a predetermined template. That's where the `Template` class plays its role.

`Template` class helps you reformat a message string into a sectioned structure and you can specify how each section is formatted. Formats include: color, alignment, font format such as bold, italic, underline,...; along with some simple transformation processing such as uppercase, title, capitalize,... All of these structures and formats are declared through a string.

From `Template`, messages are created by assigning data to predefined variables in the template string. This is like `str.format` in Python.

**Response in a `file` format**: For some operations such as exporting data, you need to reformat the data in a file format such as CSV, JSON or YAML. This type of response helps you do just that.

You can also further customize a different file format by assigning a function such as a static method to the `FileFormat` class.

The method name must be named with the prefix `write_` and declared with 3 parameters: the data to convert (a list of dict), the file descriptor object (its value can be None), and the dict as an option for conversion.

**Response in `table` format**: Table format is basically inherited from `cmd2.table_creator` to present data in row-column style.
