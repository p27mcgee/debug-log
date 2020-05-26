create_classinfo_sql = """
create table classinfo
as
select log.line, pmcl.class, pmcl.package, log.entry
from log 
join pmcl on pmcl.line = log.line
union 
select log.line, tech.class, tech.package, log.entry
from log
join tech on tech.line = log.line
"""