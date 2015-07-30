# OData to MySQL

A CLI tool for scraping OData servers into a MySQL database.

Basic help information (explanation of all the flags) can be found by running:

    python odata_mysql.py --help

More documentation available below.

## Warnings

This tool does not yet totally clean and verify all the input from the OData server, so be careful! Don't use it with an untrustworthy OData server or with a critical database.

This tool also does not currently store the links between data types (i.e. the links defined by NavigationProperty elements in OData). If you would like to add this functionality, then please go ahead! Right now, all normal data type columns are prefixed with "data:" in the MySQL column names. If you add links, perhaps you might prefix the columns related to that with "link:" or "nav:" or something.

## Documentation

Basically, this tool can be used to perform two tasks: creating tables (enabled with the `-c` flag) and downloading data (enabled with the `-d` flag). You can do these both in one call of the command, or you can do them separately.

### Creating tables

Before you can download data from the server, you need tables for them to go into. Here's the basic command you wanna run:

    python odata_mysql.py -c [-r url_of_odata_root]

This will create tables for all the data types in the first schema on the specified OData server. Currently, it is hardcoded to connect to root@localhost with password "root" and to modify a database called "odata-mysql"; there are variables near the top of the script that you can manually edit if this doesn't match your environment.

If you want to force the script to drop the tables if they already existed (as opposed to crashing), include the `--aggressive` flag (``-a``).

If you want to include all schemas on the server instead just the first one, use the `--includeallschemas` flag (`-i`) (basically, only including the first schema is a hacky workaround for Philadelphia's OData server, and this flag disables that hacky workaround).

### Downloading data

Once you have tables created, you can download into them using this command:

    python odata_mysql.py -d [-r url_of_odata_root] [-e entity_type] [-x linked_entity_type]

The `-r` flag works the same as for creating tables, but the other flags might be confusing. The `-e` flag specifies the type of entity to download; simple enough, if you want to download the permits, set it to "permits".

Let's say that the entity type "permits" can have "locations" linked to it. The OData protocol allows linked entities to be expanded and included in the output. So if you want to download all permits AND all locations linked to any permit, set the flags `-e permits -x locations`.
