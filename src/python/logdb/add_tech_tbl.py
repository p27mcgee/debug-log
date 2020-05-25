import sqlite3
import re
import src.python.logdb.createdb as createdb

# sqlite has select as instead of select into
# but we'd like to specify the schema of table tech
# more precisely thanthis allows
#     create_sql = """create table tech
#     as select
#         log.line as line,
#         case
#             when log.entry like "% - Adding %" then "add"
#             when log.entry like "% - Not putting %" then "noput"
#             when log.entry like "% - Couldn't find app for %" then "noapp"
#             else "undef"
#         end as type
#     from log
#     where log.entry like "% TechnologyClassListener]%"
# """

TECH = "tech"
NOAPP = "noapp"
NOPUT = "noput"
ADD = "add"
PWACL = "parrwebappcl"
PLATCL = "platcl"

signature_map = {
    TECH: "TechnologyClassListener]",
    NOAPP: "- Couldn't find app for ",
    NOPUT: "- Not putting ",
    ADD: "- Adding "
}

tech_types = [NOAPP, ADD, NOPUT]

class_extractors = {
    NOAPP: re.compile(r"\- Couldn't find app for ([^/]+)\/"),
    NOPUT: re.compile(r"\- Not putting (.+) in orphanage"),
    ADD: re.compile(r"\- Adding (.+) to orphanage")
}

classloader_extractors = {
    NOAPP: re.compile(r"\- Couldn't find app for [^/]+\/(.+)$"),
    NOPUT: re.compile(r"in orphanage as its from (.+)$"),
}

def initialize_tech_table(connection):
    cursor = connection.cursor()
    drop_sql = "drop table if exists tech"
    cursor.execute(drop_sql)

    create_sql = """create table tech(
        line integer primary key references log(line),
        type text,
        class text not null,
        package text not null,
        classloader text)
    """
    cursor.execute(create_sql)

    # tech_type_idx_sql = "create index idx_tech_type on tech(type)"
    # cursor.execute(tech_type_idx_sql)
    #
    # tech_package_idx_sql = "create index idx_tech_package on tech(package)"
    # cursor.execute(tech_package_idx_sql)
    #
    # tech_class_idx_sql = "create index idx_tech_class_package on tech(class, package)"
    # cursor.execute(tech_class_idx_sql)
    #
    # tech_classloader_idx_sql = "create index idx_tech_classloader on tech(classloader)"
    # cursor.execute(tech_classloader_idx_sql)

    nrows = 0
    select_tech_sql = "select line, entry from log where entry like '% TechnologyClassListener]%'"
    cursor.execute(select_tech_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(100)
        if len(rows) == 0:
            cursor.close()
            break
        add_tech_rows(rows, connection)
        nrows += len(rows)
    print("\nAdded {} rows to table tech".format(str(nrows)))


def add_tech_rows(log_tech_rows, connection):
    cursor = connection.cursor()
    insert_sql = "insert into tech (line, type, class, package, classloader) values"
    for line, entry in log_tech_rows:
        if insert_sql[-1] == ')':
            insert_sql += ","
        type = None
        for tech_type in tech_types:
            if signature_map[tech_type] in entry:
                type = tech_type
                break
        try:
            fqcn = class_extractors[type].search(entry).group(1)
        except:
            print("No match for class regex in line {} for type {} in entry: {}".format(str(line), type, entry))
            raise Exception("Failure extracting class from log line " + str(line))
        lastdot = fqcn.rfind('.')
        classname = fqcn[lastdot+1:]
        package = fqcn[:lastdot]
        try:
            if type == ADD:
                classloader = "NULL"
            else:
                classloader = "'" + classloader_extractors[type].search(entry).group(1) + "'"
        except:
            print("No match for classloader regex in line {} for type {} in entry: {}".format(str(line), type, entry))
            raise Exception("Failure extracting classloader from log line " + str(line))
        insert_sql += "\n({}, '{}', '{}', '{}', {})".format(str(line), type, classname, package, classloader)
    cursor.execute(insert_sql)
    cursor.close

# """
#         as select
#             log.line as line,
#             case
#                 when log.entry like "% - Adding %" then "add"
#                 when log.entry like "%- Not putting %" then "noput"
#                 when log.entry like "% - Couldn't find app for %" then "noapp"
#                 else "undef"
#             end as type
#         from log
#         where log.entry like "% TechnologyClassListener]%"
# """

dbname = "petclinic"

if __name__ == "__main__":
    connection = createdb.connectdb(dbname + ".db")
    initialize_tech_table(connection)