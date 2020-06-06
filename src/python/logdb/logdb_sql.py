select_multiline_entries_sql = """
select line, entry
from log
where line in (
    select distinct mesg
    from cont
    UNION
    select line from cont
)
order by line
"""

