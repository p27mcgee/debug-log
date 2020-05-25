## sqlite notes

*with python flavor*

sqlite uses `create table X as select` instead of select into.  Example usage:
```
create_sql = """create table tech
     as select
         log.line as line,
         case
             when log.entry like "% - Adding %" then "add"
             when log.entry like "% - Not putting %" then "noput"
             when log.entry like "% - Couldn't find app for %" then "noapp"
             else "undef"
         end as type
     from log
     where log.entry like "% TechnologyClassListener]%"""
```

This extracts column metadata from the query result so
the table schema cannot be explicitly specified.

