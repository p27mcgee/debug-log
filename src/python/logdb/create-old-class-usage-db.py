from os import path
import sys

from src.python.logdb.AcelShred import AcelShred
from src.python.logdb.LmclShred import LmclShred
from src.python.logdb.MesgShred import MesgShred
from src.python.logdb.createdb import create_log_db
from src.python.logdb.deprecated.PmclShred import PmclShred

log_dir = "data"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")

    debug_log = path.join(log_dir, logname + ".err")
    debug_db = path.join("", logname + ".db")
    connection = create_log_db(debug_log, debug_db)
    MesgShred().initialize_tables(connection)
    PmclShred().initialize_tables(connection)
