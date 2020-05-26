
Result: 137 rows returned in 74ms
At line 1:
select count(*) as classcount, classloader
from tech
where
type = "noapp"
group by classloader
order by classcount desc


Result: 236 rows returned in 75ms
At line 1:
select *
from tech
where
type = "noapp"
and classloader like "jdk.internal.%"
order by package


Result: 7844 rows returned in 238ms
At line 1:
select *
from tech
where
type = "noapp"
and classloader not like "jdk.internal.%"
order by package


Result: 2 rows returned in 55ms
At line 1:
select count(*) as classcount, classloader
from tech
where
type = "noapp"
and classloader not like "jdk.internal.%"
group by classloader
order by classcount desc

7085	ParallelWebappClassLoader
759	java.net.URLClassLoader@1e6060f1


Result: 207 rows returned in 1474ms
At line 1:
select count(*) as classcount, pmcl.location, tech.classloader
from tech
join pmcl
on tech.class = pmcl.class
and tech.package = pmcl.package
and tech.type = "noapp"
group by pmcl.location, tech.classloader
order by classcount desc


Result: 72 rows returned in 254ms
At line 1:
select count(*) as classcount, pmcl.location, tech.classloader
from tech
join pmcl
on tech.class = pmcl.class
and tech.package = pmcl.package
and tech.type = "noapp"
and pmcl.location <> "NULL_ProtectionDomain"
group by pmcl.location, tech.classloader
order by tech.classloader


Result: 60 rows returned in 311ms
At line 1:
select count(*) classcount, pmcl.location
from
pmcl
join classinfo
on pmcl.line = classinfo.line
group by pmcl.location


Result: 1 rows returned in 581ms
At line 1:
select count(*) as classcount, tech.classloader
from
pmcl
join classinfo
on classinfo.line == pmcl.line
join tech
on tech.class = pmcl.class
and tech.package = pmcl.package
and pmcl.location == "NULL_ProtectionDomain"
group by tech.classloader
order by classcount desc

170	ParallelWebappClassLoader
*these 170 classes are all proxies and lambdas


Result: 78 rows returned in 256ms
At line 1:
select *
from
pmcl
join classinfo on classinfo.line = pmcl.line
and pmcl.location == "NULL_ProtectionDomain"
where
pmcl.line not in (
select p.line from
pmcl as p
join tech as t
on t.class = p.class
and t.package = p.package
)

These additional location == "NULL_ProtectionDomain" classes
without matching tech entries are:
UNTOUCHABLE jdk reflection classes
more lambdas


Result: 189 rows returned in 192ms
At line 1:
select pmcl.*
from pmcl
join classinfo on pmcl.line = classinfo.line
where pmcl.location not like "%WEB-INF%"
order by pmcl.package

The 189 non- WEB-INF location classes should not be associated
with the app.  These appear to be just about all Tomcat supplied
classes.