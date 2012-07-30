create table sp_scheduled_tasks (
    id serial not null primary key,
    task_name varchar(100),
    description text,
    active boolean default false,
    in_progress boolean default false,
    executed boolean default false,
    just_one_time boolean default false,
    period integer, --in minutes
    last_execution datetime,
    task_date date,
    task_time time,
    monday boolean default false,
    tuesday boolean default false,
    wednesday boolean default false,
    thursday boolean default false,
    friday boolean default false,
    saturday boolean default false,
    sunday boolean default false,
    attempts integer default 0,
    max_attempts integer default 0,
    executable varchar(100),
    data text
);