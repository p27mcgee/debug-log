import re
import sys
from os import path
import src.python.logdb.createdb as createdb
from src.python.logdb.Shred import Shred
from src.python.logdb.Shred import ShredTableCreator
from src.python.logdb.Shred import ShredEntrySelector
from src.python.logdb.Shred import ShredEntryClassifier
from src.python.logdb.Shred import ShredValueExtractor

class AmqpShred(Shred):
    tbl_name = 'amqp'
    create_tbl_sql = """
create table amqp(
line integer primary key references log(line),
type text not null,
exchangeName text not null,
queueName text not null,
properties text not null,
body text not null)
"""
    tbl_index_sqls = [
    ]
    tbl_creator = ShredTableCreator(tbl_name, create_tbl_sql, tbl_index_sqls)

    entry_signature = "AMQP Publisher] DEBUG - MQPublisherImpl#publish call: exchangeName:"
    entry_selector = ShredEntrySelector(entry_signature)

    entry_classifier = ShredEntryClassifier()   # just one default type

    extracted_val_names=['exchangeName', 'queueName', 'properties', 'body']
    value_extractors = {
        Shred.DEFAULT_TYPE: re.compile(r"^.* AMQP Publisher] DEBUG - MQPublisherImpl#publish call: exchangeName: (?P<exchangeName>[^,]*), queueName: (?P<queueName>[^,]*), properties: (?P<properties>.*), body: (?P<body>.*)$")
    }
    value_extractor = ShredValueExtractor(extracted_val_names, value_extractors)

    insert_columns = ['line', 'type', 'exchangeName', 'queueName', 'properties', 'body']

    type_extractor = re.compile(r".*, type=(?P<type>[^,]+), ")

    def __init__(self):
        super().__init__(
            tbl_creator=AmqpShred.tbl_creator,
            entry_selector=AmqpShred.entry_selector,
            entry_classifier=AmqpShred.entry_classifier,
            value_extractor=AmqpShred.value_extractor,
            insert_columns=AmqpShred.insert_columns
            )

    def transform_values(self, line, entry, type, extracted_vals):
        match = AmqpShred.type_extractor.search(entry)
        return line, match.group('type'), extracted_vals['exchangeName'], extracted_vals['queueName'], extracted_vals['properties'], extracted_vals['body']

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_db = path.join("", logname + ".db")
    connection = createdb.connectdb(debug_db)
    amqpShred = AmqpShred()
    amqpShred.initialize_tables(connection)
