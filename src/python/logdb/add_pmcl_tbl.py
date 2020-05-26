import sqlite3
import re
import src.python.logdb.createdb as createdb
from src.python.logdb.createdb import classAndPackage
from src.python.logdb.createdb import quotOrNull

PMCL = "pmcl"
OK = "ok"
KO = "ko"

signature_map = {
    PMCL: "!PM!ClassLoad|",
    OK: "|classloader=",
    KO: "|exception=",
}

pmcl_types = [OK, KO]
value_extractors = {
    OK: re.compile(r"\!PM\!ClassLoad\|(?P<fqcn>[^|]+)\|classloader\=(?P<classloader>[^&]+)\&location\=(?P<location>[^&]+)\&result\=(?P<result>.+)(?P<exception>~NOEXCP~)?$"),
    KO: re.compile(r"\!PM\!ClassLoad\|(?P<fqcn>[^|]+)\|exception\=(?P<exception>.+)(?P<classloader>~NOCL~)?(?P<location>~NOLOC~)?(?P<result>~NORSLT~)?$")
}

def initialize_pmcl_table(connection):
    cursor = connection.cursor()

    drop_sql = "drop table if exists pmcl"
    cursor.execute(drop_sql)

    create_sql = """create table pmcl(
        line integer primary key references log(line),
        type text,
        class text not null,
        package text not null,
        classloader text,
        location text,
        result text,
        exception text)
    """
    cursor.execute(create_sql)

    # add indexes
    pmcl_type_idx_sql = "create index idx_pmcl_type on pmcl(type)"
    cursor.execute(pmcl_type_idx_sql)
    pmcl_package_idx_sql = "create index idx_pmcl_package on pmcl(package)"
    cursor.execute(pmcl_package_idx_sql)
    pmcl_class_idx_sql = "create index idx_pmcl_class_package on pmcl(class, package)"
    cursor.execute(pmcl_class_idx_sql)
    pmcl_classloader_idx_sql = "create index idx_pmcl_classloader on pmcl(classloader)"
    cursor.execute(pmcl_classloader_idx_sql)

    # populate
    nrows = 0
    select_pmcl_sql = "select line, entry from log where entry like '%!PM!ClassLoad%'"
    cursor.execute(select_pmcl_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(500)
        if len(rows) == 0:
            cursor.close()
            break
        add_pmcl_rows(rows, connection)
        nrows += len(rows)
    print("\nAdded {} rows to table pmcl".format(str(nrows)))

def add_pmcl_rows(log_pmcl_rows, connection):
    cursor = connection.cursor()
    insert_sql = "insert into pmcl (line, type, class, package, classloader, location, result, exception) values"
    for line, entry in log_pmcl_rows:
        if insert_sql[-1] == ')':
            insert_sql += ","
        type = None
        for pmcl_type in pmcl_types:
            if signature_map[pmcl_type] in entry:
                type = pmcl_type
                break
        try:
            fqcn, classloader, location, result, exception = value_extractors[type].search(entry).group('fqcn', 'classloader', 'location', 'result', 'exception')
        except:
            print("No match for extractor regex in line {} for type {} in entry: {}".format(str(line), type, entry))
            if not "|java.lang.String|" in entry:
                raise Exception("Failure extracting data from log line " + str(line))
            else:
                # String is weird.  Ignore it and move on
                continue
        classname, package = classAndPackage(fqcn)
        insert_sql += "\n({}, '{}', '{}', '{}', {}, {}, {}, {})".format(str(line), type, classname, package, quotOrNull(classloader), quotOrNull(location), quotOrNull(result), quotOrNull(exception))
    cursor.execute(insert_sql)
    cursor.close

dbname = "petclinic"

if __name__ == "__main__":
    connection = createdb.connectdb(dbname + ".db")
    initialize_pmcl_table(connection)