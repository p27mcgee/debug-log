create_classinfo_tbl_sql = """
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

remove_tech_noput_classes_from_classinfo_sql = """
delete from classinfo
where
line in (
    select line
    from tech
    where
    type = "noput"
    union
    select pmcl.line
    from pmcl
    join tech
    on tech.class = pmcl.class
    and tech.package = pmcl.package
    where tech.type = "noput"
)
"""

remove_tech_noapp_not_PWCL_classes_from_classinfo_sql = """
delete from classinfo
where
line in (
    select line
    from tech
    where
    type = "noapp" and classloader <> "ParallelWebappClassLoader"
    union
    select pmcl.line
    from pmcl
    join tech
    on tech.class = pmcl.class
    and tech.package = pmcl.package
    and tech.type = "noapp" and tech.classloader <> "ParallelWebappClassLoader"
)
"""

remove_pmcl_NULL_ProtectionDomain_classes_from_classinfo_sql = """
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
"""

remove_pmcl_result_UNTOUCHABLE_sql = """
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
and pmcl.result == "UNTOUCHABLE"
)
"""

select_web_app_location_joined_on_classinfo_package_counts = """
select count(*) as classcount, location, pmcl.package
from pmcl
join classinfo
on pmcl.line = classinfo.line
group by location, pmcl.package
order by pmcl.package
"""

select_webinf_location_package_counts = """
select count(*) as classcount, location, pmcl.package
from pmcl
where 
location like "%WEB-INF%"
group by location, pmcl.package
order by pmcl.package
"""

select_multiline_messages = """
select log.line, log.entry
from log
where line in (
select line
from cont
union 
select distinct mesg
from cont
)
"""