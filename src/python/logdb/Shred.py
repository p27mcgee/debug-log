import sqlite3
import re
from abc import ABC, abstractmethod

# import src.python.logdb.createdb as createdb
# from src.python.logdb.createdb import classAndPackage

class Shred(ABC):
    #    log_tbl_name = 'log'
    DEFAULT_TYPE = "default"

    def __init__(self,
                 tbl_name,
                 create_tbl_sql,
                 tbl_index_sqls=None,
                 entry_signature=None,
                 types=None,
                 type_signatures=None,
                 select_entries_sql=None,
                 extracted_val_names=None,
                 value_extractors=None,
                 insert_columns=None,
                 insert_sql=None,
                 misfits_tbl_name=None,
                 quiet=False,
                 show_misfits=False
                 ):
        self.tbl_name = tbl_name
        self.create_tbl_sql = create_tbl_sql
        if tbl_index_sqls is None:
            self.tbl_index_sqls = []
        else:
            self.tbl_index_sqls = tbl_index_sqls
        self.drop_tbl_sql = "drop table if exists " + self.tbl_name
        if entry_signature is None:
            # matches every log entry
            self.entry_signature = ''
        else:
            self.entry_signature = entry_signature
        if types is None:
            # just one type
            self.types = [Shred.DEFAULT_TYPE]
        else:
            self.types = types
        if type_signatures is None:
            # every log entry matches default type
            self.type_signatures = {Shred.DEFAULT_TYPE: ''}
        else:
            self.type_signatures = type_signatures
        if select_entries_sql is None:
            self.select_entries_sql = "select line, entry from log where entry like '%{}%'".format(self.entry_signature)
        else:
            self.select_entries_sql = select_entries_sql
        if extracted_val_names is None:
            # no values extracted from the entry
            self.extracted_val_names = []
        else:
            self.extracted_val_names = extracted_val_names
        if value_extractors is None:
            # no values extracted from the entry
            self.value_extractors = {Shred.DEFAULT_TYPE: re.compile('')}
        else:
            self.value_extractors = value_extractors
        if insert_columns is None:
            if (len(types) > 1):
                insert_columns = ['line', 'type'] + extracted_val_names
            else:
                insert_columns = ['line'] + extracted_val_names
        else:
            self.insert_columns = insert_columns
        if insert_sql is None:
            # insert into tbl (line, type, colA) values (?, ?, ?)
            self.insert_sql = "insert into {} (".format(self.tbl_name)
            for col in self.insert_columns:
                if not self.insert_sql.endswith("("):
                    self.insert_sql += ", "
                self.insert_sql += col
            self.insert_sql += ") values (?"
            for n in range(len(self.insert_columns)-1):
                self.insert_sql += ", ?"
            self.insert_sql += ")"
        else:
            self.insert_sql = insert_sql
        if misfits_tbl_name is None:
            self.misfits_tbl_name = tbl_name + "_misfits"
        else:
            self.misfits_tbl_name = misfits_tbl_name
        self.create_misfits_sql = "create table {}( line integer primary key references log(line))".format(self.misfits_tbl_name)
        self.drop_misfits_sql = "drop table if exists " + self.misfits_tbl_name
        self.insert_misfits_sql = "insert into {} (line) values (?)".format(self.misfits_tbl_name)
        self.quiet = quiet
        self.show_misfits = show_misfits
        super().__init__()


    def transform_values(self, line, entry, type, extracted_vals):
        classname, package = self.classAndPackage(extracted_vals["fqcn"])
        return line, type, classname, package, extracted_vals["application"], extracted_vals["location"]

    def initialize_tables(self, connection):
        cursor = connection.cursor()
        self.create_table(cursor)
        self.create_misfits_table(self, cursor)
        cursor.close()
        self.populate_tables(connection)

    def create_table(self, cursor):
        cursor.execute(self.drop_table_sql)
        cursor.execute(self.create_sql)
        for index_sql in self.table_index_sqls:
            cursor.execute(index_sql)

    def create_misfits_table(self, cursor):
        cursor.execute(self.drop_misfits_sql)
        cursor.execute(self.create_misfits_sql)

    def populate_tables(self, connection):
        cursor = connection.cursor()
        totalAdded = 0
        totalMisfits = 0
        cursor.execute(self.select_entries_sql)
        while True:
            print(".", end="")
            rows = cursor.fetchmany(1000)
            if len(rows) == 0:
                cursor.close()
                break
            nAdded, nMisfits = self.add_rows(rows, connection)
            totalAdded += nAdded
            totalMisfits += nMisfits
        if not self.quiet:
            print("\nAdded {} rows to table {}".format(str(totalAdded), self.tbl_name))
            print("Added {} rows to table {}".format(str(totalMisfits), self.misfits_tbl_name))
        cursor.close()

    def add_rows(self, log_rows, connection):
        cursor = connection.cursor()
        cursor.execute("begin transaction")
        values = []
        misfits = []
        nAdded = 0
        nMisfits = 0
        for line, entry in log_rows:
            type = self.find_type(entry)
            extractor = self.value_extractors[type]
            try:
                match = extractor.search(entry)
                extracted_vals = {}
                for extracted_val_name in self.extracted_val_names:
                    extracted_vals[extracted_val_name] = match.group(extracted_val_name)
                values.append(self.transform_values(line, entry, type, extracted_vals))
                nAdded += 1
            except:
                if self.show_misfits:
                    print("No match for extractor regex in entry line {}: {}".format(str(line), entry))
                misfits.append((line,))
                nMisfits += 1
        cursor.executemany(self.insert_sql, values);
        cursor.executemany(self.insert_misfits_sql, misfits);
        cursor.execute("commit")
        cursor.close()
        return nAdded, nMisfits

    def find_type(self, entry):
        for type in self.types:
            if self.type_signatures[type] in entry:
                return type
        return Shred.DEFAULT_TYPE