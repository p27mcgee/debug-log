
* also removes jdk reflection classes


Result: query executed successfully. Took 62ms, 418 rows affected
At line 1:
delete from classinfo
where
line in (
select line
from pmcl
where pmcl.location == "NULL_ProtectionDomain"
union
select tech.line
from tech
join pmcl
on tech.class = pmcl.class
and tech.package = pmcl.package
and pmcl.location == "NULL_ProtectionDomain"
)