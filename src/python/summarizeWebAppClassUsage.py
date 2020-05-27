from os import path
from urllib.parse import unquote as urldecode
from src.python.logdb.createdb import connectdb
import src.python.logdb.logdb_sql as logdb_sql
import json

def web_app_class_usage_joined_on_classinfo_json(cursor, output_json):
    locprefix = ""
    prefixlen = 0
    class_summary = {}
    for classcount, location, package in cursor.execute(logdb_sql.select_web_app_location_joined_on_classinfo_package_counts):
        if prefixlen == 0 and "apache-tomcat" in location:
            decoded_location = urldecode(location)
            tomcat_at = decoded_location.find("/apache-tomcat")
            if tomcat_at != -1:
                locprefix = decoded_location[:tomcat_at+1]
                prefixlen = len(locprefix)
        dec_loc = urldecode(location)
        if (prefixlen != 0 and dec_loc.startswith(locprefix)):
            dec_loc = dec_loc[prefixlen:]
        if not dec_loc in class_summary:
            class_summary[dec_loc] = {}
        class_summary[dec_loc][package] = classcount
    add_usage_totals(class_summary)
    with open(output_json, "w") as outfile:
        json.dump(class_summary, outfile, sort_keys=True, indent=4)

def web_app_class_usage_in_webinf(cursor, output_json):
    locprefix = ""
    prefixlen = 0
    class_summary = {}
    for classcount, location, package in cursor.execute(logdb_sql.select_webinf_location_package_counts):
        if prefixlen == 0 and "apache-tomcat" in location:
            decoded_location = urldecode(location)
            tomcat_at = decoded_location.find("/apache-tomcat")
            if tomcat_at != -1:
                locprefix = decoded_location[:tomcat_at+1]
                prefixlen = len(locprefix)
        dec_loc = urldecode(location)
        if (prefixlen != 0 and dec_loc.startswith(locprefix)):
            dec_loc = dec_loc[prefixlen:]
        if not dec_loc in class_summary:
            class_summary[dec_loc] = {}
        class_summary[dec_loc][package] = classcount
    add_usage_totals(class_summary)
    with open(output_json, "w") as outfile:
        json.dump(class_summary, outfile, sort_keys=True, indent=4)

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
    class_summary[" Total"] = app_total
    class_summary[" Source count"] = loc_count

db_name = "petclinic"
db_ext = ".db"
db_dir = ""

json_joined_on_classinfo = "class-usage-joined-on-classinfo.json"
json_in_webinf = "class-usage-in-webinf.json"

def main(db_path):
    connection = connectdb(db_path)
    cursor = connection.cursor()
    web_app_class_usage_in_webinf(cursor, json_in_webinf)
    with open(json_in_webinf, "r") as infile:
        for line in infile:
            print(line, end="")

    # this provides a validation of the WEB-INF location approach but
    # is less accurate and less tolerant of different servlet containers
    # web_app_class_usage_joined_on_classinfo_json(cursor, json_joined_on_classinfo)

if __name__ == "__main__":
    db_path = path.join(db_dir, db_name + db_ext)
    main(db_path)


