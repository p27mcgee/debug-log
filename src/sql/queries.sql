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

-- select the begining and end of requests
select *
from mesg
where
    logger = 'HttpManager' and message like '!LM!RequestTime|RequestEnded|uri=%'
    or  -- (logger = 'CapturingHttpItem' or logger = 'b')
    logger = 'CapturingHttpItem' and message like 'CRUMB request@%' || X'09' || X'09' || X'09' || 'BEGIN%'
order by line

--select overflow/timeout indicatioins
SELECT *
FROM mesg
WHERE false
	 OR message like '%Maximum source events reached for this context.%'
	 OR message like '%Ignoring propagator %'
	 OR message like '%Cleared expired assessment context%'
	 OR message like '%Removing expired key=%'
	 OR message like '%Removing long-living runnable%'

-- select triggers
SELECT *
FROM mesg
WHERE
    logger = 'ContrastDataFlowTriggerDispatcherImpl'
    AND message = X'09' || 'TRACE PLUG'

-- select triggers and continuation lines
-- this is ugly can it be generalized to not repeat the trigger line selection?  TODO
select log.*
from log
where
    line in (
        SELECT line
        FROM mesg
        WHERE
            logger = 'ContrastDataFlowTriggerDispatcherImpl'
            AND message = X'09' || 'TRACE PLUG'
        UNION
        SELECT line
        from cont
        WHERE
            mesg in (
                SELECT line
                FROM mesg
                WHERE
                    logger = 'ContrastDataFlowTriggerDispatcherImpl'
                    AND message = X'09' || 'TRACE PLUG'
            )
    )
order by log.line

-- select vulnerability findings
select *
from mesg
where logger = 'QueueFindingListener'
    and message like 'Added finding for rule ID:%'

-- path-traversal findings regardless of reporting status
select *
from mesg
where logger = 'Finding'
    and message like '!LM!TraceFate|%|ruleId=path-traversal'

-- deduplicated findings
select *
from mesg
where logger = 'Finding'
    and message like '!LM!TraceFate|LocalCacheHit|%'

-- preflighted findings
select *
from mesg
where logger = 'Finding'
    and message like '!LM!TraceFate|Preflighted|%'

-- select unterminated requests or responses
select *
from crumb
where crumb."type" = 'req_begin'
   and crumb.req NOT IN (SELECT req from crumb where crumb."type" = 'hist_req_begin')
UNION ALL
select *
from crumb
where crumb."type" = 'resp_begin'
   and crumb.resp NOT IN (SELECT resp from crumb where crumb."type" = 'hist_resp_begin')
