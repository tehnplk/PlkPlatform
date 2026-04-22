-- Delete one visit by VN only.
-- No offline_track / pcu_dw_track / vn_stat_log.
-- Adjust @vn before running.

set @vn = '690422224521';
set @screen_hos_guid = (select hos_guid from opdscreen where vn = @vn limit 1);

-- Rows keyed by vn
delete from opitemrece where vn = @vn;
delete from opitemrece_summary where vn = @vn;
delete from incoth where vn = @vn;
delete from fbshistory where vn = @vn;
delete from inc_opd_stat where vn = @vn;
delete from ovstdiag where vn = @vn;
delete from opi_dispense where hos_guid = @screen_hos_guid;
delete from opdscreen where vn = @vn;
delete from visit_pttype where vn = @vn;
delete from dt_list where vn = @vn;
delete from vn_insert where vn = @vn;
delete from vn_stat_signature where vn = @vn;
delete from ovst_seq where vn = @vn;
delete from vn_stat where vn = @vn;
delete from ovst where vn = @vn;

-- Optional checks
select 'ovst' as tbl, count(*) as c from ovst where vn = @vn
union all
select 'vn_stat', count(*) from vn_stat where vn = @vn
union all
select 'ovstdiag', count(*) from ovstdiag where vn = @vn
union all
select 'opdscreen', count(*) from opdscreen where vn = @vn
union all
select 'opitemrece', count(*) from opitemrece where vn = @vn
union all
select 'opitemrece_summary', count(*) from opitemrece_summary where vn = @vn
union all
select 'incoth', count(*) from incoth where vn = @vn
union all
select 'fbshistory', count(*) from fbshistory where vn = @vn
union all
select 'inc_opd_stat', count(*) from inc_opd_stat where vn = @vn
union all
select 'visit_pttype', count(*) from visit_pttype where vn = @vn
union all
select 'dt_list', count(*) from dt_list where vn = @vn
union all
select 'vn_insert', count(*) from vn_insert where vn = @vn
union all
select 'vn_stat_signature', count(*) from vn_stat_signature where vn = @vn
union all
select 'ovst_seq', count(*) from ovst_seq where vn = @vn;
