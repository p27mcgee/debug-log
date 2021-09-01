import re
from abc import ABC, abstractmethod
import contextlib

class Shred(ABC):
    #    log_tbl_name = 'log'
    DEFAULT_TYPE = "default"
    SHOW_PROGRESS = False

    def __init__(self,
                 tbl_creator,
                 entry_selector,
                 entry_classifier,
                 value_extractor,
                 insert_columns=None,
                 insert_sql=None,
                 insert_misfits_sql=None,
                 quiet=False,
                 show_misfits=False
                 ):
        self.tbl_creator = tbl_creator
        self.entry_selector = entry_selector
        self.entry_classifier = entry_classifier
        self.value_extractor = value_extractor
        if insert_columns is None:
            if (len(self.entry_classifier.types) > 1):
                self.insert_columns = ['line', 'type'] + self.value_extractor.extracted_val_names
            else:
                self.insert_columns = ['line'] + self.value_extractor.extracted_val_names
        else:
            self.insert_columns = insert_columns
        if insert_sql is None:
            # insert into tbl (line, type, colA) values (?, ?, ?)
            self.insert_sql = "insert into {} (".format(self.tbl_creator.tbl_name)
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
        if insert_misfits_sql is None:
            self.insert_misfits_sql = "insert into {} (line) values (?)".format(self.tbl_creator.misfits_tbl_name)
        else:
            self.insert_misfits_sql = insert_misfits_sql
        self.quiet = quiet
        self.show_misfits = show_misfits
        super().__init__()

    @abstractmethod
    def transform_values(self, line, entry, type, extracted_vals):
        pass

    def transform_misfits(self, line, last_good_line):
        return (line,)

    def initialize_tables(self, connection):
        self.tbl_creator.create_empty_table(connection)
        self.tbl_creator.create_empty_misfits_table(connection)
        self.populate_tables(connection)

    def populate_tables(self, connection):
            totalAdded = 0
            totalMisfits = 0
            last_good_line = -1
            if not self.quiet:
                print("Shredding to {}...".format(self.tbl_creator.tbl_name))
            for rows in self.entry_selector.select_batches(connection):
                if not self.quiet and self.SHOW_PROGRESS:
                        print(".", end="")
                nAdded, nMisfits, last_good_line = self.add_rows(rows, last_good_line, connection)
                totalAdded += nAdded
                totalMisfits += nMisfits
            if not self.quiet:
                if self.SHOW_PROGRESS:
                    print("\n")
                print("Added {} rows to table {}".format(str(totalAdded), self.tbl_creator.tbl_name))
                print("Added {} rows to table {}".format(str(totalMisfits), self.tbl_creator.misfits_tbl_name))

    def add_rows(self, log_rows, last_good_line, connection):
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute("begin transaction")
            values = []
            misfits = []
            nAdded = 0
            nMisfits = 0
            for line, entry in log_rows:
                type = self.entry_classifier.find_type(entry)
                try:
                    extracted_vals = self.value_extractor.extract_values(type, entry, line)
                    insert_vals = self.transform_values(line, entry, type, extracted_vals)
                    values.append(insert_vals)
                    last_good_line = line
                    nAdded += 1
                except:
                    if self.show_misfits:
                        print("Extraction/transformation failed in entry line {}: {}".format(str(line), entry))
                    misfit_vals = self.transform_misfits(line, last_good_line)
                    misfits.append(misfit_vals)
                    nMisfits += 1
            cursor.executemany(self.insert_sql, values)
            cursor.executemany(self.insert_misfits_sql, misfits)
            cursor.execute("commit")
        return nAdded, nMisfits, last_good_line


    def classAndPackage(self, fqcn):
        lastdot = fqcn.rfind('.')
        classname = fqcn[lastdot + 1:]
        package = fqcn[:lastdot]
        return classname, package


class ShredTableCreator:

    def __init__(self,
                 tbl_name,
                 create_tbl_sql,
                 tbl_index_sqls=None,
                 misfits_tbl_name=None, # pass empty string "" for no misfits table
                 create_misfits_sql=None,
                 misfits_index_sqls=None
                 ):
        self.tbl_name = tbl_name
        self.create_tbl_sql = create_tbl_sql
        if tbl_index_sqls is None:
            self.tbl_index_sqls = []
        else:
            self.tbl_index_sqls = tbl_index_sqls
        self.drop_tbl_sql = "drop table if exists " + self.tbl_name

        if misfits_tbl_name is None:
            self.misfits_tbl_name = tbl_name + "_misfits"
        else:
            self.misfits_tbl_name = misfits_tbl_name
        if create_misfits_sql is None:
            self.create_misfits_sql = "create table {}( line integer primary key references log(line))".format(
                self.misfits_tbl_name)
        else:
            self.create_misfits_sql = create_misfits_sql
        if misfits_index_sqls is None:
            self.misfits_index_sqls = []
        else:
            self.misfits_index_sqls = misfits_index_sqls
        self.drop_misfits_sql = "drop table if exists " + self.misfits_tbl_name
        super().__init__()

    def create_empty_table(self, connection):
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(self.drop_tbl_sql)
            cursor.execute(self.create_tbl_sql)
            for index_sql in self.tbl_index_sqls:
                cursor.execute(index_sql)

    def create_empty_misfits_table(self, connection):
        if self.misfits_tbl_name:
            with contextlib.closing(connection.cursor()) as cursor:
                cursor.execute(self.drop_misfits_sql)
                cursor.execute(self.create_misfits_sql)
                for index_sql in self.misfits_index_sqls:
                    cursor.execute(index_sql)


class ShredEntrySelector:

    def __init__(self,
                 entry_signature=None,
                 select_entries_sql=None,
                 batch_size=1000):
        if entry_signature is None:
            # matches every log entry
            self.entry_signature = ''
        else:
            self.entry_signature = entry_signature
        if select_entries_sql is None:
            self.select_entries_sql = "select line, entry from log where entry like '%{}%'".format(self.entry_signature)
        else:
            self.select_entries_sql = select_entries_sql
        self.batch_size = batch_size
        super().__init__()

    def select_batches(self, connection):
        with contextlib.closing(connection.cursor()) as cursor:
            cursor.execute(self.select_entries_sql)
            while True:
                rows = cursor.fetchmany(self.batch_size)
                if len(rows) == 0:
                    break
                yield rows


class ShredEntryClassifier:

    def __init__(self, type_signatures=None):
        if type_signatures is None:
            # every log entry matches default type
            self.type_signatures = {Shred.DEFAULT_TYPE: ''}
        else:
            self.type_signatures = type_signatures
        self.types = self.type_signatures.keys()
        super().__init__()

    def find_type(self, entry):
        for type, signature in self.type_signatures.items():
            if signature in entry:
                return type
        return Shred.DEFAULT_TYPE


class ShredValueExtractor:

    def __init__(self,
                 extracted_val_names=None,
                 value_extractors=None, ):
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
        super().__init__()

    def extract_values(self, type, entry, line=None):
        extracted_vals = {}
        extractor = self.value_extractors[type]
        if extractor:
            match = extractor.search(entry)
            for extracted_val_name in self.extracted_val_names:
                extracted_vals[extracted_val_name] = match.group(extracted_val_name)
        return extracted_vals