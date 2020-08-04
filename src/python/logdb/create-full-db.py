from os import path
import sys

from src.python.logdb.AcelShred import AcelShred
from src.python.logdb.AmqpShred import AmqpShred
from src.python.logdb.LmclShred import LmclShred
from src.python.logdb.MesgShred import MesgShred
from src.python.logdb.createdb import create_log_db

logname = "old-war-petclinic"
log_dir = "data"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    debug_log = path.join(log_dir, logname + ".log")
    debug_db = path.join("", logname + ".db")
    connection = create_log_db(debug_log, debug_db)
    MesgShred().initialize_tables(connection)
    LmclShred().initialize_tables(connection)
    AcelShred().initialize_tables(connection)
    AmqpShred().initialize_tables(connection)
