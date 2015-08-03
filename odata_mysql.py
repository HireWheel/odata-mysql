#!/usr/bin/python

# The MIT License (MIT)
#
# Copyright (c) 2015 HireWheel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from lxml import etree
import requests
import sys
import argparse
import MySQLdb
import logging as log
import pprint


# MySQL details
DB_SERVER = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_DATABASE = "odata-mysql"

# requests details
REQ_USER_AGENT = "odata_mysql.py"
REQ_BASE_HEADERS = {
	'User-Agent': REQ_USER_AGENT
}

# character encoding defaults. don't mess with this stuff!
DB_DEFAULT_CHARSET = "utf8"
DB_DEFAULT_COLLATION = "utf8_unicode_ci"


# mapping MySQL types to categories
DB_TYPES_NUMERIC = (
	"INTEGER",
	"INT",
	"SMALLINT",
	"TINYINT",
	"MEDIUMINT",
	"BIGINT",
	"DECIMAL",
	"NUMERIC",
	"FLOAT",
	"DOUBLE",
	"BIT",
	"BOOL",
	"BOOLEAN",
	"SERIAL",
	"DEC",
	"FIXED",
	"DOUBLE PRECISION",
	"REAL"
)
DB_TYPES_DATEANDTIME = (
	"DATE",
	"DATETIME",
	"TIMESTAMP",
	"TIME",
	"YEAR"
)


# OData server details
OD_ROOT = "http://services.odata.org/V3/OData/OData.svc"

# OData allows some types to have unlimited size, but MySQL doesn't
# support this, so we have to set arbitrary defaults for when a
# size isn't specified by the OData server
OD_DEFAULT_STRING_LENGTH = "65535"
OD_DEFAULT_DECIMAL_PRECISION = "65"
OD_DEFAULT_DECIMAL_SCALE = "30"

# probably shouldn't touch these
OD_NAMESPACES = {
	"atom": "http://www.w3.org/2005/Atom",
	"d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
	"edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
	"edm": "http://schemas.microsoft.com/ado/2008/09/edm",
	"m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
}

# mapping OData types to printf type specifiers
OD_TYPES_i = (
	"Edm.Int16",
	"Edm.Int32",
	"Edm.Int64",
	"Edm.SByte",
	"Edm.Boolean"
)
OD_TYPES_d = (
	"Edm.Bytes"
)
OD_TYPES_s = (
	"Edm.String",
	"Edm.Date",
	"Edm.DateTime",
	"Edm.DateTimeOffset",
	"Edm.Decimal"
)
OD_TYPES_f = (
	"Edm.Double"
)


# generates tables for all entity types in the OData server's first schema
# set aggressive=True to drop old tables
# set includeAllSchemas=True to include more than just the first schema
def generateCreateTableQueries(**kwargs):

	aggressive = False
	if "aggressive" in kwargs:
		aggressive = kwargs["aggressive"]

	includeAllSchemas = False
	if "includeAllSchemas" in kwargs:
		includeAllSchemas = kwargs["includeAllSchemas"]

	odRoot = OD_ROOT
	if "odRoot" in kwargs:
		odRoot = kwargs["odRoot"]


	url = odRoot + "/$metadata"
	#log.info("Getting metadata from %s",url)

	req = requests.get(url, headers=REQ_BASE_HEADERS)
	root = etree.fromstring(req.content)

	schemas = root.xpath("/edmx:Edmx/edmx:DataServices/edm:Schema", namespaces=OD_NAMESPACES)

	queries = []

	for schema in schemas:
		namespace = schema.get("Namespace")

		# schemaName = DB_SCHEMA_PREFIX + namespace

		# if aggressive:
		# 	dropDbSql = "DROP SCHEMA IF EXISTS " + schemaName
		# 	queries.append(dropDbSql)

		# dbSql = "CREATE SCHEMA IF NOT EXISTS " + schemaName
		# queries.append(dbSql)

		entityTypes = schema.xpath("edm:EntityType", namespaces=OD_NAMESPACES)

		for entityType in entityTypes:

			# TODO: sanitize entityTypeName
			entityTypeName = entityType.get("Name")

			if aggressive:
				dropTblSql = "DROP TABLE IF EXISTS " + entityTypeName
				queries.append(dropTblSql)

			query = "CREATE TABLE "
			query += entityTypeName
			query += "("

			querySegments = []

			properties = entityType.xpath("edm:Property", namespaces=OD_NAMESPACES)

			for p in properties:

				odName = p.get("Name")
				sqlName = "data:" + odName

				odType = p.get("Type")

				sqlType = None
				sqlSize = None
				sqlIsSigned = True
				sqlHasDefaultValue = False # not yet implemented!!
				sqlDefaultValue = None
				sqlIsNullable = p.get("Nullable", default=True)

				if "DefaultValue" in p.keys():
					sqlHasDefaultValue = True
					sqlDefaultValue = p.get("DefaultValue")


				if odType == "Edm.Boolean":
					sqlType = "TINYINT"
					sqlSize = "1"

				elif odType == "Edm.Byte":
					sqlType = "TINYINT"
					sqlIsSigned = False

				elif odType == "Edm.SByte":
					sqlType = "TINYINT"

				elif odType == "Edm.Int16":
					sqlType = "SMALLINT"

				elif odType == "Edm.Int32":
					sqlType = "INT"

				elif odType == "Edm.Int64":
					sqlType = "BIGINT"

				elif odType == "Edm.Date":
					sqlType = "DATE"

				elif odType == "Edm.DateTime":
					sqlType = "DATETIME"

				elif odType == "Edm.String":
					sqlType = "VARCHAR"
					sqlSize = p.get("MaxLength", default=OD_DEFAULT_STRING_LENGTH)

				elif odType == "Edm.Decimal":
					sqlType = "DECIMAL"

					precision = p.get("Precision", default=OD_DEFAULT_DECIMAL_PRECISION)
					scale = p.get("Scale", default=OD_DEFAULT_DECIMAL_SCALE)
					scale = min(scale, precision)

					sqlSize = precision + "," + scale

				else:
					log.warning("Unknown data type: %s", odType)
					sqlType = "VARCHAR"
					sqlSize = "65535"


				# build the SQL query from the sql variables
				pSql = ""
				pSql += "`" + sqlName + "`"
				pSql += " " + sqlType

				if sqlSize != None:
					pSql += "(" + sqlSize + ")"

				if sqlType in DB_TYPES_NUMERIC:
					if not sqlIsSigned:
						pSql += " UNSIGNED"
					# else:
					# 	pSql += " SIGNED"

				if not sqlIsNullable:
					pSql += " NOT NULL"

				# TODO: implement default values

				querySegments.append(pSql)


			# add key constraints
			# currently only supports primary key constraints
			keys = entityType.xpath("Key")

			for key in keys:


				kSql = ""
				kSql += "PRIMARY KEY ("

				propRefs = key.xpath("PropertyRef")

				isFirstPropRef = True
				for propRef in propRefs:
					if isFirstPropRef:
						isFirstPropRef = False
					else:
						kSql += ", "
					kSql += propRef.get("Name")

				kSql += ")"
				querySegments.append(kSql)




			# add all the keys and properties to the query
			isFirstSegment = True
			for seg in querySegments:
				if isFirstSegment:
					isFirstSegment = False
				else:
					query += ", "
				query += seg


			query += ")"
			query += " CHARACTER SET " + DB_DEFAULT_CHARSET
			query += " COLLATE " + DB_DEFAULT_COLLATION

			log.debug("Ready to create table %s", entityTypeName)

			queries.append(query)

		if not includeAllSchemas:
			break

	return queries


def createTables(con, **kwargs):

	cur = con.cursor()

	queries = generateCreateTableQueries(**kwargs)

	log.info("Creating tables...")

	for query in queries:
		cur.execute(query)

	con.commit()
	log.info("Created %i tables!", len(queries))



def insertAllEntities(con, entityType, expandTypes=None, **kwargs):

	retryOn5xx = False
	if "retryOn5xx" in kwargs:
		retryOn5xx = kwargs["retryOn5xx"]

	odRoot = OD_ROOT
	if "odRoot" in kwargs:
		odRoot = kwargs["odRoot"]

	log.info("Beginning batch download for %s (expand: %s)...", entityType, expandTypes)

	cur = con.cursor()

	nextUrl = odRoot + "/" + entityType
	if expandTypes != None:
		nextUrl += "?$expand=" + expandTypes

	hasRetriedFor5xx = False

	while nextUrl != None:

		log.debug("Querying %s...", nextUrl)

		req = requests.get(
			nextUrl,
			headers = REQ_BASE_HEADERS
		)

		# retry the same url if we get a 500 error
		if req.status_code >= 500:
			if retryOn5xx and not hasRetriedFor5xx:
				log.warning("Received 5xx error, retrying request...")
				hasRetriedFor5xx = True
				continue
			else:
				log.error("Server returned a 5xx error; script likely to crash!")
		else:
			hasRetriedFor5xx = False

		nextUrl = None

		root = etree.fromstring(req.content)

		nextLink = root.xpath("/atom:feed/atom:link[@rel='next']", namespaces=OD_NAMESPACES)

		if len(nextLink) > 0:
			nextUrl = nextLink[0].get("href")

		entries = root.xpath("/atom:feed//atom:entry", namespaces=OD_NAMESPACES)

		for entry in entries:

			insertEntity(cur, entry)
			con.commit()

	log.info("Finished batch download!")


# TODO: handle duplicate rows
def insertEntity(cur, entry):
	propertyElements = entry.xpath("atom:content/m:properties/d:*", namespaces=OD_NAMESPACES)

	# TODO: make this more flexible (and more readable)
	entityType = entry.xpath("atom:category/@term", namespaces=OD_NAMESPACES)[0].split(".")[1]

	props = []
	propCols = []
	propVals = []
	propDataTypes = []

	for p in propertyElements:

		tag = p.tag
		tagSplit = tag.split("}")
		tag = tagSplit[len(tagSplit) - 1]

		col = "data:" + tag

		val = None
		if p.get("m:null", default=False) != "true":
			val = p.text

		dataType = p.get("m:type", default=None)

		prop = {
			"col": col,
			"val": val,
			"dataType": dataType
		}
		props.append(prop)


	# begin constructing the sql query
	sqlData = []

	sql = ""
	sql += "INSERT INTO " + entityType

	# output all the column names
	sql += "("
	isFirstCol = True
	for prop in props:
		if isFirstCol:
			isFirstCol = False
		else:
			sql += ", "
		sql += "`" + prop["col"] + "`"
	sql += ")"

	# output all the column data
	sql += " VALUES ("
	isFirstVal = True
	for prop in props:
		if isFirstVal:
			isFirstVal = False
		else:
			sql += ", "

		val = prop["val"]

		# TODO: sanitize more data than just int-like types

		typeSpecifier = "%s"
		if prop["dataType"] != None:
			if prop["dataType"] in OD_TYPES_d:
				typeSpecifier += "%d"
			elif prop["dataType"] in OD_TYPES_f:
				typeSpecifier += "%f"
			elif prop["dataType"] in OD_TYPES_s:
				typeSpecifier += "%s"
			elif prop["dataType"] in OD_TYPES_i:
				typeSpecifier += "%i"
				val = sanitizeIntLike(val)

		sql += typeSpecifier

		sqlData.append(val)

	sql += ")"

	cur.execute(sql, sqlData)



def sanitizeIntLike(raw):
	if raw.lower() == "true":
		return 1
	if raw.lower() == "false":
		return 0
	return int(raw)



parser = argparse.ArgumentParser(description='Import from OData to MySQL.')
parser.add_argument(
	"-c", "--createtables", help="create tables?", action="store_true")
parser.add_argument(
	"-d", "--downloaddata", help="download data?", action="store_true")
parser.add_argument(
	"-r", "--odataroot", help="root of OData server", default=OD_ROOT)
parser.add_argument(
	"-b", "--database", help="name of MySQL database to use", default=DB_DATABASE)
parser.add_argument(
	"-e", "--entitytype", help="type of entity to batch query", default=None)
parser.add_argument(
	"-x", "--expandtypes", help="type(s) of entity to expand, separated by commas", default=None)
parser.add_argument(
	"-a", "--aggressive", help="drop tables if already exist?", action="store_true")
parser.add_argument(
	"-i", "--includeallschemas", help="query all schemas instead of just first?", action="store_true")
parser.add_argument(
	"-y", "--retryon5xx", help="retry when the server returns a 5xx error?", action="store_true")
args = parser.parse_args()


log.basicConfig(format='%(levelname)s: %(message)s', level=log.DEBUG)

con = MySQLdb.connect(
	DB_SERVER,
	DB_USER,
	DB_PASS,
	args.database,
	use_unicode=True,
	charset=DB_DEFAULT_CHARSET
)

with con:

	odRoot = args.odataroot
	odRoot.rstrip("/") # trailing slashes are evil!


	if args.createtables:
		argsCreateTables = {
			"aggressive": args.aggressive,
			"includeAllSchemas": args.includeallschemas,
			"odRoot": args.odataroot
		}
		createTables(con, **argsCreateTables)

	if args.downloaddata:
		if args.entitytype != None:
			argsInsertEntities = {
				"retryOn5xx": args.retryon5xx,
				"odRoot": args.odataroot
			}
			insertAllEntities(con, args.entitytype, args.expandtypes, **argsInsertEntities)
