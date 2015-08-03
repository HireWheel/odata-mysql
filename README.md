# OData to MySQL

A CLI tool for downloading from an OData server into a MySQL database.

This tool was developed for working with specific datasets provided by various government agencies, and as such, features have only been added as needed. Pull requests with new features are welcome; please be sure to follow the coding style already used in the existing code and to keep your commit history relatively clean and orderly.

Basic help information (explanation of all the flags) can be found by running:

    python odata_mysql.py --help

More documentation available below.

## Warnings

This tool does not yet totally clean and verify all the input from the OData server, so be careful! Don't use it with an untrustworthy OData server or with a critical database.

This tool also does not currently store the links between data types (i.e. the links defined by NavigationProperty elements in OData). If you would like to add this functionality, feel free to fork and pull request. Right now, all normal data type columns are prefixed with "data:" in the MySQL column names. If you add links, perhaps you might prefix the columns related to that with "link:" or "nav:" or something.

## Documentation

Basically, this tool can be used to perform two tasks: creating tables (enabled with the `-c` flag) and downloading data (enabled with the `-d` flag). You can do these both in one call of the command, or you can do them separately.

### Important flags

Whether you are creating tables or downloading data, you will probably need to include an OData root and MySQL details.

To include an OData root, pass the URL with the `-r` flag. Your URL should include the schema (i.e. http/https) and may or may not include a trailing slash. If no OData root is specified, it defaults to `http://services.odata.org/V3/OData/OData.svc`.

By default, this script uses the database "odata-mysql" on the localhost MySQL with "root" as both the username and password. To change this, pass a MySQL URI with the `-u` flag. Your URI should be in this format: `mysql://USER:PASS@HOST:PORT/DATABASE`. The script will use typical defaults for any values missing from your URI (if you omit the password, it will prompt you to enter it).

Alternatively, if you would like to use the default MySQL server/user/password, but would like to specify an alternate database name, you can omit the `-u` flag and instead pass `-b [name_of_database]`.

### Creating tables

Before you can download data from the server, you need tables for them to go into. Here's the basic command you wanna run:

    python odata_mysql.py -c [-r odata_root] [-u mysql_uri]

This will create tables for all the data types in the first schema on the specified OData server. Currently, it is hardcoded to connect to root@localhost with password "root" and to modify a database called "odata-mysql"; there are variables near the top of the script that you can manually edit if this doesn't match your environment.

If you want to force the script to drop the tables if they already existed (as opposed to crashing), include the `--aggressive` flag (``-a``).

If you want to include all schemas on the server instead just the first one, use the `--includeallschemas` flag (`-i`) (basically, only including the first schema is a hacky workaround for [Philadelphia's OData server](http://phlapi.com), and this flag disables that hacky workaround).

### Downloading data

Once you have tables created, you can download into them using this command:

    python odata_mysql.py -d [-e entity_type] [-x linked_entity_type] [-y] [-r odata_root] [-u mysql_uri]

The `-r` flag works the same as for creating tables, but the other flags might be confusing. The `-e` flag specifies the type of entity to download; simple enough, if you want to download the permits, set it to "permits".

Let's say that the entity type "permits" can have "locations" linked to it. The OData protocol allows linked entities to be expanded and included in the output. So if you want to download all permits AND all locations linked to any permit, set the flags `-e permits -x locations`.

The `-y` flag tells the script to retry a request once if it gets a 5xx error (i.e. an internal server error).

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
