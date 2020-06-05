import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred

class AcelShred(Shred):
    tbl_name = "acel"
    create_tbl_sql = \
"""create table acel(
line integer primary key references log(line),
type text not null, 
class text not null,
package text not null,
application text,
location text)"""
    tbl_index_sqls = [
                           "create index idx_acel_package on acel(package)",
                           "create index idx_acel_class_package on acel(class, package)"
                       ]

    entry_signature = " ApplicationClassEventListener] "

    types = ["noput", "noapp", "orphan", "uninventoried", "contains", "adopted", "used"]
    type_signatures = {
        "noput": "- Not putting ",
        "noapp": "- Couldn't find app for ",
        "orphan": " to orphanage",
        "uninventoried": "missed classload events",
        "contains": "- url @detectLibraryClass",
        "adopted": "from orphanage by CodeSource path",
        "used": " to library usage for lib ",
    }

    extracted_val_names=["fqcn", "location", "application"]
    value_extractors = {
        # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
        "noput": re.compile(
            r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<location>~NOLOC~)?(?P<application>~NOAPP~)?"),
        # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
        "noapp": re.compile(
            r"\- Couldn't find app for (?P<fqcn>\S+) with CodeSource path (?P<application>~NOAPP~)?(?P<location>.*)$"),
        # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
        "orphan": re.compile(r"\- Adding (?P<fqcn>\S+) to orphanage(?P<location>~NOLOC~)?(?P<application>~NOAPP~)?$"),
        # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
        "uninventoried": re.compile(
            r"\- Adding (?P<fqcn>\S+) to list of missed classload events for uninventoried (?P<location>~NOLOC~)?(?P<application>.*)$"),
        # - url @detectLibraryClass vfs:/opt/jboss/server/default/deploy/jbossweb.sar/jbossweb.jar/ contains org.apache.tomcat.util.buf.C2BConverter for application "platform-servlet"
        "contains": re.compile(
            r"\- url \@detectLibraryClass (?P<location>.+) contains (?P<fqcn>\S+) for application \"(?P<application>.*)\"$"),
        # - Took {} from orphanage by CodeSource path {} and passing to app {}
        "adopted": re.compile(
            r"\- Took (?P<fqcn>\S+) from orphanage by CodeSource path (?P<location>.+) and passing to app \"(?P<application>.*)\"$"),
        # - Adding {} to library usage for lib {} in application "{}""
        "used": re.compile(
            r"\- Adding (?P<fqcn>\S+) to library usage for lib (?P<jarname>\S+) in app (?P<location>~NOLOC~)?\"(?P<application>.*)\"$"),
        # default type will be a misfit
        Shred.DEFAULT_TYPE: re.compile(r"^~NOMATCH~$")
    }

    insert_columns = ["line", "type", "class", "package", "application", "location"]


    def __init__(self):
        super().__init__(tbl_name=AcelShred.tbl_name,
                         create_tbl_sql=AcelShred.create_tbl_sql,
                         tbl_index_sqls=AcelShred.tbl_index_sqls,
                         entry_signature=AcelShred.entry_signature,
                         types=AcelShred.types,
                         type_signatures=AcelShred.type_signatures,
                         extracted_val_names=AcelShred.extracted_val_names,
                         value_extractors=AcelShred.value_extractors,
                         insert_columns=AcelShred.insert_columns
                         )

    def transform_values(self, line, entry, type, extracted_vals):
        classname, package = self.classAndPackage(extracted_vals["fqcn"])
        return line, type, classname, package, extracted_vals["application"], extracted_vals["location"]

    def classAndPackage(self, fqcn):
        lastdot = fqcn.rfind('.')
        classname = fqcn[lastdot + 1:]
        package = fqcn[:lastdot]
        return classname, package


logname = "petclinic"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    acelShred = AcelShred()
    acelShred.initialize_tables(connection)
