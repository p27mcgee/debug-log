-- create a table containing only multi-line log messages
select log.*
from log
where line in (
	select mesg
	from cont
	UNION
	select line
	from cont)
order by line
