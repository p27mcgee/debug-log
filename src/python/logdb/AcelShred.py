import re
import src.python.logdb.Shred as Shred

class AcelShred(Shred):

    def __init__(self):
        super().__init__(tbl_name="acel",
                         create_tbl_sql=
"""
create table acel(
 line integer primary key references log(line),
 type text not null, 
 class text not null,
 package text not null,
 application text,
 location text)
""",
                         table_index_sqls=[
                             "create index idx_acel_package on acel(package)",
                             "create index idx_acel_class_package on acel(class, package)"
                         ],
                         entry_signature=" ApplicationClassEventListener] ",
                         types=["noput", "noapp", "addding", "contains"],
                         type_signatures={
                             "noput": "- Not putting ",
                             "noapp": "- Couldn't find app for ",
                             "addding": "- Adding ",
                             "contains": "- url @detectLibraryClass"
                         },
                         extracted_val_names=["fqcn", "location", "application"],
        value_extractors = {
            # - Not putting java.util.Hashtable$KeySet in orphanage as its from bootstrapped classloade
            "noput": re.compile(
                r"\- Not putting (?P<fqcn>\S+) in orphanage as its from (?P<location>~NOLOC~)?(?P<application>~NOAPP~)?"),
            # - Couldn't find app for org.jboss.Main$ShutdownHook with CodeSource location file:/opt/jboss/bin/run.jar
            "noapp": re.compile(
                r"\- Couldn't find app for (?P<fqcn>\S+) with CodeSource location (?P<application>~NOAPP~)?(?P<location>.*)$"),
            # - Adding org.apache.tomcat.util.buf.C2BConverter to list of missed classload events for uninventoried platform-servlet
            "addding": re.compile(
                r"\- Adding (?P<fqcn>\S+) to list of missed classload events for uninventoried (?P<location>~NOLOC~)?(?P<application>.*)$"),
            # - url @detectLibraryClass vfs:/opt/jboss/server/default/deploy/jbossweb.sar/jbossweb.jar/ contains org.apache.tomcat.util.buf.C2BConverter for application "platform-servlet"
            "contains": re.compile(
                r"\- url \@detectLibraryClass (?P<location>.*) contains (?P<fqcn>\S+) for application \"(?P<application>.*)\"$"),
            # default type will be a misfit
            Shred.DEFAULT_TYPE: re.compile(r"^~NOMATCH~$")
        },
        insert_columns=["line", "type", "classname", "package", "application", "location"])

        def transform_values(self, line, entry, type, extracted_vals):
            classname, package = self.classAndPackage(extracted_vals["fqcn"])
            return line, type, classname, package, extracted_vals["application"], extracted_vals["location"]
