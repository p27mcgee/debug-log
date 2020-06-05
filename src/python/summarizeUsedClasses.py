import sys
from os import path
from urllib.parse import unquote as urldecode
from src.python.logdb.createdb import connectdb
import src.python.logdb.logdb_sql as logdb_sql
import json

select_used_class_package_counts = """
select count(*) as classcount, cont.location, used.package
from acel as used
left join acel as cont
on used.class = cont.class and
used.package = cont.package AND
cont.type = "contains"
where 
used.type = "used"
group by cont.location, used.package
"""
# there are 4 of these bootstrap classes
#   file:/Users/philmcgee/Run/Squad/prod35/pet-clinic-home/spring-petclinic/target/spring-petclinic-2.3.0.BUILD-SNAPSHOT.jar
# the actual libraries look like this
#   jar:file:/Users/philmcgee/Run/Squad/prod35/pet-clinic-home/spring-petclinic/target/spring-petclinic-2.3.0.BUILD-SNAPSHOT.jar!/BOOT-INF/classes!/
def web_app_class_usage(cursor, output_json):
    class_summary = {}
    for classcount, location, package in cursor.execute(select_used_class_package_counts):
        trimmed_loc = trim_location_prefix(location)
        if not trimmed_loc in class_summary:
            class_summary[trimmed_loc] = {}
        class_summary[trimmed_loc][package] = classcount
    add_usage_totals(class_summary)
    with open(output_json, "w") as outfile:
        json.dump(class_summary, outfile, sort_keys=True, indent=4)

def trim_location_prefix(location):
    if "target/" in location:
        target_at = location.find("target/")
        locprefixlen = target_at + len("target/")
        return location[locprefixlen:]
    else:
        return location

def add_usage_totals(class_summary):
    app_total = 0
    loc_total = 0
    loc_count = len(class_summary)
    for loc in class_summary:
        for count in class_summary[loc].values():
            loc_total += count
            app_total += count
        class_summary[loc][" Total"] = loc_total
        loc_total = 0;
    class_summary[" Total classes"] = app_total
    class_summary[" Libraries"] = loc_count

json_file = "class-usage-standalone.json"

def main(db_path):
    connection = connectdb(db_path)
    cursor = connection.cursor()
    web_app_class_usage(cursor, json_file)
    with open(json_file, "r") as infile:
        for line in infile:
            print(line, end="")

logname = "san-sb-petclinic"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    db_path = path.join("", logname + ".db")
    main(db_path)

