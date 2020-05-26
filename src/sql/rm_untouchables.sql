
Untouchable classes include com.contrastsecurity.* and jdk reflection classes


Result: query executed successfully. Took 43ms, 318 rows affected
At line 1:
delete from classinfo
where
line in (
select line
from pmcl
where pmcl.result == "UNTOUCHABLE"
union
select tech.line
from tech
join pmcl
on tech.class = pmcl.class
and tech.package = pmcl.package
and pmcl.result == "UNTOUCHABLE")
)