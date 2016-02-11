drop table if exists all_hosts;
create table all_hosts (
  hostname text primary key not null,
  status text,
  build text,
  timestamp text
);
