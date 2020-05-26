from os import path
from urllib.parse import unquote as urldecode
from src.python.logdb.createdb import connectdb
import src.python.logdb.logdb_sql as logdb_sql
import json

def summarize_web_app_class_usage(cursor):
    print("\nThe log database classinfo and pmcl tables include the following Web App classes:")
    locprefix = ""
    prefixlen = 0
    for classcount, location, package in cursor.execute(logdb_sql.select_web_app_location_package_counts):
        if prefixlen == 0 and "apache-tomcat" in location:
            decoded_location = urldecode(location)
            tomcat_at = decoded_location.find("/apache-tomcat")
            if tomcat_at != -1:
                locprefix = decoded_location[:tomcat_at+1]
                prefixlen = len(locprefix)
        dec_loc = urldecode(location)
        if (prefixlen != 0 and dec_loc.startswith(locprefix)):
            dec_loc = dec_loc[prefixlen:]
        print("{} classes in package {} from {}".format(str(classcount), package, dec_loc))

def web_app_class_usage_json(cursor):
#    print("\nThe log database classinfo and pmcl tables include the following Web App classes:")
    locprefix = ""
    prefixlen = 0
    class_summary = {}
    for classcount, location, package in cursor.execute(logdb_sql.select_web_app_location_package_counts):
        if prefixlen == 0 and "apache-tomcat" in location:
            decoded_location = urldecode(location)
            tomcat_at = decoded_location.find("/apache-tomcat")
            if tomcat_at != -1:
                locprefix = decoded_location[:tomcat_at+1]
                prefixlen = len(locprefix)
        dec_loc = urldecode(location)
        if (prefixlen != 0 and dec_loc.startswith(locprefix)):
            dec_loc = dec_loc[prefixlen:]
#        print("{} classes in package {} from {}".format(str(classcount), package, dec_loc))
        if not dec_loc in class_summary:
            class_summary[dec_loc] = {}
        class_summary[dec_loc][package] = classcount
    # add totals
    app_total = 0
    loc_total = 0
    for loc in class_summary:
        for count in class_summary[loc].values():
            loc_total += count
            app_total += count
        class_summary[loc][" Total"] = loc_total
        loc_total = 0;
    class_summary[" Total"] = app_total
    with open("class-usage.json", "w") as outfile:
        json.dump(class_summary, outfile, sort_keys=True, indent=4)

db_name = "petclinic"
db_ext = ".db"
db_dir = ""

if __name__ == "__main__":
    db_path = path.join(db_dir, db_name + db_ext)
    connection = connectdb(db_path)
    cursor = connection.cursor()
    web_app_class_usage_json(cursor)


