select pmcl.line, tech.class, tech.package, pmcl.result, pmcl.location, pmcl.classloader
from tech
join pmcl
on pmcl.class = tech.class and pmcl.package = tech.package
where tech.type = "noput"
and (pmcl.classloader <> "NULL_LOADER" or pmcl.location <> "NULL_ProtectionDomain" )