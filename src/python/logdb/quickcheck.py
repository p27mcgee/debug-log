import createdb
import sys
import contextlib
from src.python.logdb.MesgShred import MesgShred

TELLS = [
            ("MAX_CONTEXT_SOURCE_EVENTS", "Maximum source events reached for this context."),
             ("MAX_CONTEXT_PROPAGATION_EVENTS", "Ignoring propagator "),
             ("MAX_TRACE_TTL", "Cleared expired assessment context"),
             ("MAX_TRACE_TTL", "Removing expired key="),
             ("CONTEXT_MAP_PURGE_TIMEOUT", "Removing long-living runnable")
        ]

def reportTells(connection):
    qrystr = """SELECT entry 
FROM log
WHERE 
    line in (
         SELECT line 
         FROM mesg 
         WHERE false"""

    for tell in TELLS:
        qrystr += "\n\t OR message like '%{}%'".format(tell[1])
    qrystr += ")\nORDER BY line;"
    # print(qrystr);

    with contextlib.closing(connection.cursor()) as cursor:
        cursor.execute(qrystr)
        print("Found {} log entries of concern.".format(max(cursor.rowcount,0)))
        # print("Found {} log entries of concern.".format("{FIXME! max(cursor.rowcount,0)}"))
        while True:
            row = cursor.fetchone()
            if row == None:
                break
            print(row)

def main(logname):
    connection = createdb.main(logname)
    MesgShred().initialize_tables(connection)
    reportTells(connection)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logname = sys.argv[1]
    else:
        raise Exception("Missing command line parameter for log name.")
    main(logname)