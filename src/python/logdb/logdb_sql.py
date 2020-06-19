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

select_busiest_loggers = """
select count(*) as n, logger
from mesg
group by logger
order by n desc
"""

count_mesgs_at_level = """
select count(*), level
from mesg
group by level
"""

select_comms = """
select log.*
from log
join mesg
on mesg.line = log.line and mesg.logger = "wire"
order by log.line
"""

# headers just repeat the HTTP headers already included in wire
# with a slightly different format
select_comms_plus_headers = """
select log.*
from log
join mesg
on mesg.line = log.line and (mesg.logger = "wire" or mesg.logger = "header")
order by log.line
"""