# OData to MySQL

A CLI tool for downloading from an OData server into a MySQL database.

This tool was developed for working with specific datasets provided by various government agencies, and as such, features have only been added as needed. Pull requests with new features are welcome; please be sure to follow the coding style already used in the existing code and to keep your commit history relatively clean and orderly.

Basic help information (explanation of all the flags) can be found by running:

    python odata_mysql.py --help

More documentation available below.

## Warnings

This tool does not yet totally clean and verify all the input from the OData server, so be careful! Don't use it with an untrustworthy OData server or with a critical database.

This tool also does not currently store the links between data types (i.e. the links defined by NavigationProperty elements in OData). If you would like to add this functionality, feel free to fork and pull request. Right now, all normal data type columns are prefixed with "data_" in the MySQL column names. If you add links, perhaps you might prefix the columns related to that with "link_" or "nav_" or something.

## Flags

Whether you are creating tables or downloading data, the following flags can (and most likely should) be used.

### OData root

To include an OData root, pass the URL with the `-r` flag. Your URL should include the schema (i.e. http/https) and may or may not include a trailing slash. If no OData root is specified, it defaults to `http://services.odata.org/V3/OData/OData.svc`.

### MySQL URI

By default, this script connects to the database at `mysql://root:root@localhost:3306/odata-mysql`. To change this, pass a MySQL URI with the `-u` flag. Your URI should be in this format: `mysql://USER:PASS@HOST:PORT/DATABASE`. The script will use typical defaults for any values missing from your URI (if you omit the password, it will prompt you to enter it).

Alternatively, if you would like to use the default MySQL server/user/password, but would like to specify an alternate database name, you can omit the `-u` flag and instead pass `-b [name_of_database]`. (if, for whatever strange reason, you include both flags, `-b` has precedence over the database name in the `-u` flag)

### Entity type

Use the `-e` flag to specify the name of the data type on the OData server you would like to download. This flag is required if you are downloading data (i.e. with `-d`); however, if you are only creating tables (i.e. with `-c`), you can omit this flag and it will create tables for all data types in the first schema on the server.

If you are downloading data, there is also a similar flag for expanding entity types, `-x`. This will use the `$expand` parameter in OData to download additional entity types besides the main type you are downloading. For example, let's say you want to download all "permits", but permits have "locations" attached to them, and you want to download all locations as well. The command you'd use for this is `-e permits -x locations`. The `-x` flag also allows you to list multiple tables by simply separating the table names with columns

#### Aliases

By default, this script uses the name of the entities on the OData server as the name of their table in the MySQL database. If you would like to use alternate table names, you can specify an alternate name for the entity type (i.e. the `-e` value) with the `-l` flag, and alternate names for the expand types (i.e. the `-x` values) with the `-k` flag (like the `-x` flag, the `-k` flag supports multiple values separated by commas).


## Commands

Basically, this tool can be used to perform two tasks: creating tables (enabled with the `-c` flag) and downloading data (enabled with the `-d` flag). You can do these both in one call of the command, or you can do them separately.

### Creating tables

Before you can download data from the server, you need tables for them to go into. Here's the basic command you wanna run:

    python odata_mysql.py -c [-e entity_type] [-r odata_root] [-u mysql_uri]

This will create tables for all the data types in the first schema on the specified OData server. If you include an entity_type with the `-e` flag, it will only create a table for that data type.

If you want to force the script to drop the tables if they already existed (as opposed to crashing), include the `--aggressive` flag (``-a``).

If you want to include all schemas on the server instead just the first one, use the `--includeallschemas` flag (`-i`) (basically, only including the first schema is a hacky workaround for [Philadelphia's OData server](http://phlapi.com), and this flag disables that hacky workaround).

### Downloading data

Once you have tables created, you can download into them using this command:

    python odata_mysql.py -d [-e entity_type] [-x linked_entity_type] [-y] [-r odata_root] [-u mysql_uri]

The `-r` flag works the same as for creating tables, but the other flags might be confusing. The `-e` flag specifies the type of entity to download; simple enough, if you want to download the permits, set it to "permits".

Let's say that the entity type "permits" can have "locations" linked to it. The OData protocol allows linked entities to be expanded and included in the output. So if you want to download all permits AND all locations linked to any permit, set the flags `-e permits -x locations`.

The `-y` flag tells the script to retry a request once if it gets a 5xx error (i.e. an internal server error).

## Examples

This documentation is a bit complex and confusing, so here's an example. This connects to the OData server for [Philadelphia Open Data](http://phlapi.com). It creates tables for permits and locations, then downloads all permits, as well as all locations attached to any permit. It stores the permits in a MySQL table called "PhillyPermit" and the locations in a MySQL table called "PhillyLocation", and both of these tables are created in a MySQL database called "my_awesome_database". The `-y` flag is also included in case the API throws an internal server error (which this particular server is sometimes prone to do). Here's the full command:

    python odata_mysql.py -c -d -r http://api.phila.gov/li/v1 -b my_awesome_database -e permits -l PhillyPermit -x locations -k PhillyLocation -y

If you prefer, here's a more verbose form of the exact same command:

    python odata_mysql.py --createtables --downloaddata --odataroot http://api.phila.gov/li/v1 --databasename my_awesome_database --entitytype permits --entitytable PhillyPermit --expandtypes locations --expandtables PhillyLocation --retryon5xx

## License

The MIT License (MIT)

Copyright (c) 2015 HireWheel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
