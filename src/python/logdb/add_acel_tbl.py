import sqlite3
import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.createdb import classAndPackage
from urllib.parse import unquote as urldecode

DEFAULT_TYPE = "default"
entry_signature = " ApplicationClassEventListener] "
types = ["noput", "noapp", "orphan", "uninventoried", "contains", "used"]
type_signatures = {
    "noput": "- Not putting ",
    "noapp": "- Couldn't find app for ",
    "orphan": " to orphanage",
    "uninventoried": "missed classload events",
    "contains": "- url @detectLibraryClass",
    "used": "- url @detectLibraryClass"
}
extracted_val_names = ["fqcn", "location", "application"]
value_extractors = {
    # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
    "noput": re.compile(r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<location>~NOLOC~)?(?P<application>~NOAPP~)?"),
    # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
    "noapp": re.compile(r"\- Couldn't find app for (?P<fqcn>\S+) with CodeSource path (?P<application>~NOAPP~)?(?P<location>.*)$"),
    # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
    "orphan": re.compile(r"\- Adding (?P<fqcn>\S+) to orphanage(?P<location>~NOLOC~)?(?P<application>~NOAPP~)?$"),
    # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
    "uninventoried": re.compile(r"\- Adding (?P<fqcn>\S+) to list of missed classload events for uninventoried (?P<location>~NOLOC~)?(?P<application>.*)$"),
    # - url @detectLibraryClass vfs:/opt/jboss/server/default/deploy/jbossweb.sar/jbossweb.jar/ contains org.apache.tomcat.util.buf.C2BConverter for application "platform-servlet"
    "contains": re.compile(r"\- url \@detectLibraryClass (?P<location>.*) contains (?P<fqcn>\S+) for application \"(?P<application>.*)\"$"),
    # - Adding {} to library usage for lib {} in application "{}""
    "used": re.compile(r"\- Adding (?P<fqcn>\S+) to library usage for lib (?P<location>.*)  in application \"(?P<application>.*)\"$"),
    # default type will be a misfit
    DEFAULT_TYPE : re.compile(r"^~NOMATCH~$")
}
# ignore ClassLoader noapps as misfits
# - Couldn't find app for org.jboss.profileservice.deployment.hotdeploy.HDScanner$HDScanAction with ClassLoader "BaseClassLoader@1d824a0b{profile-classloader:0.0.0$MODULE}"

table_name = "acel"
misfits_table_name = table_name + "_misfits"
select_entries_sql = "select line, entry from log where entry like '%" + entry_signature + "%'"

drop_table_sql = "drop table if exists " + table_name
create_sql = """create table acel(
        line integer primary key references log(line),
        type text not null, 
        class text not null,
        package text not null,
        application text,
        location text)
    """
table_index_sqls = [
    "create index idx_" + table_name + "_package on " + table_name + "(package)",
    "create index idx_" + table_name + "_class_package on " + table_name + "(class, package)"
]
insert_sql = "insert into " + table_name + " (line, type, class, package, application, location) values (?, ?, ?, ?, ?, ?)"

drop_misfits_sql = "drop table if exists " + misfits_table_name
create_misfits_sql = "create table " + misfits_table_name + "(line integer primary key references log(line))"
insert_misfits_sql = "insert into " + misfits_table_name + " (line) values (?)"

def transform_values(line, entry, type, extracted_vals):
    classname, package = classAndPackage(extracted_vals["fqcn"])
    return line, type, classname, package, extracted_vals["application"], extracted_vals["location"]

def initialize_tables(connection):
    cursor = connection.cursor()
    create_table(cursor)
    create_misfits_table(cursor)
    cursor.close()
    populate_tables(connection)

def create_table(cursor):
    cursor.execute(drop_table_sql)
    cursor.execute(create_sql)
    for index_sql in table_index_sqls:
        cursor.execute(index_sql)

def create_misfits_table(cursor):
    cursor.execute(drop_misfits_sql)
    cursor.execute(create_misfits_sql)

def populate_tables(connection):
    cursor = connection.cursor()
    totalAdded = 0
    totalMisfits = 0
    cursor.execute(select_entries_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(1000)
        if len(rows) == 0:
            cursor.close()
            break
        nAdded, nMisfits = add_rows(rows, connection)
        totalAdded += nAdded
        totalMisfits += nMisfits
    print("\nAdded {} rows to table {}".format(str(totalAdded), table_name))
    print("Added {} rows to table {}".format(str(totalMisfits), misfits_table_name))
    cursor.close()

def add_rows(log_rows, connection):
    cursor = connection.cursor()
    cursor.execute("begin transaction")
    values = []
    misfits = []
    nAdded = 0
    nMisfits = 0
    for line, entry in log_rows:
        type = find_type(entry)
        extractor = value_extractors[type]
        try:
            match = extractor.search(entry)
            extracted_vals = {}
            for extracted_val_name in extracted_val_names:
                extracted_vals[extracted_val_name] = match.group(extracted_val_name)
            values.append(transform_values(line, entry, type, extracted_vals))
            nAdded += 1
        except:
            # print("No match for extractor regex in entry line {}: {}".format(str(line), entry))
            misfits.append((line,))
            nMisfits += 1
    cursor.executemany(insert_sql, values);
    cursor.executemany(insert_misfits_sql, misfits);
    cursor.execute("commit")
    cursor.close()
    return nAdded, nMisfits

def find_type(entry):
    for type in types:
        if type_signatures[type] in entry:
            return type
    return DEFAULT_TYPE

def initialize_acel_table(connection):
    initialize_tables(connection)

logname = "petclinic"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    initialize_acel_table(connection)
