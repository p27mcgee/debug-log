import sqlite3
import re
import src.python.logdb.createdb as createdb

TECH = "tech"
NOAPP = "noapp"
NOPUT = "noput"
ADD = "add"

signature_map = {
    TECH: "TechnologyClassListener]",
    NOAPP: "- Couldn't find app for ",
    NOPUT: "- Not putting ",
    ADD: "- Adding "
}

tech_types = [NOAPP, ADD, NOPUT]
value_extractors = {
    NOAPP: re.compile(r"- Couldn't find app for (?P<fqcn>[^/]+)\/(?P<classloader>.+)$"),
    NOPUT: re.compile(r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<classloader>.+)$"),
    ADD: re.compile(r"\- Adding (?P<fqcn>\S+) to orphanage(?P<classloader>~NOCL~)?")
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

    # add indexes
    tech_type_idx_sql = "create index idx_tech_type on tech(type)"
    cursor.execute(tech_type_idx_sql)
    tech_package_idx_sql = "create index idx_tech_package on tech(package)"
    cursor.execute(tech_package_idx_sql)
    tech_class_idx_sql = "create index idx_tech_class_package on tech(class, package)"
    cursor.execute(tech_class_idx_sql)
    tech_classloader_idx_sql = "create index idx_tech_classloader on tech(classloader)"
    cursor.execute(tech_classloader_idx_sql)

    # populate
    nrows = 0
    select_tech_sql = "select line, entry from log where entry like '% TechnologyClassListener]%'"
    cursor.execute(select_tech_sql)
    while True:
        print(".", end="")
        rows = cursor.fetchmany(500)
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
            fqcn, classloader = value_extractors[type].search(entry).group('fqcn', 'classloader')
            if classloader == None:
                classloader = "NULL"
            else:
                classloader = "'" + classloader + "'"
        except:
            print("No match for extractor regex in line {} for type {} in entry: {}".format(str(line), type, entry))
            raise Exception("Failure extracting class from log line " + str(line))
        lastdot = fqcn.rfind('.')
        classname = fqcn[lastdot+1:]
        package = fqcn[:lastdot]
        insert_sql += "\n({}, '{}', '{}', '{}', {})".format(str(line), type, classname, package, classloader)
    cursor.execute(insert_sql)
    cursor.close

dbname = "petclinic"

if __name__ == "__main__":
    connection = createdb.connectdb(dbname + ".db")
    initialize_tech_table(connection)