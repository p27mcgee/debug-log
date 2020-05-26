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


Result: query executed successfully. Took 2622ms, 4102 rows affected
At line 1:
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