Result: query executed successfully. Took 57ms, 1990 rows affected
At line 1:
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