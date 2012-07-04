-- __code__ = sp_logs index on table_name and row_id
-- __desc__ = Increase speed on sp_logs searches

create index sp_logs_table_name_row_id
  on sp_logs
  using btree(table_name, row_id);