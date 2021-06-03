
-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob


do $$
<<first_block>>
declare
  ln_count integer := 0;
begin
   -- Check if user exists

   select count(*)
   into ln_count
   from pg_user
   where usename = 'minous';

   if ln_count = 0 then
     CREATE user minous password 'minous';
   end if;

   select count(*)
   into ln_count
   from pg_user
   where usename = 'vcbe_dba';

   if ln_count = 0 then
     CREATE user vcbe_dba password 'vcbe_dba';
   end if;

   select count(*)
   into ln_count
   from pg_user
   where usename = 'cims_ro';

   if ln_count = 0 then
     CREATE user cims_ro password 'cims_ro';
   end if;

end first_block $$;
-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


GRANT CONNECT ON DATABASE vcbe_db to minous;
GRANT CONNECT ON DATABASE vcbe_db to cims_ro;

-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event (
  id SERIAL NOT NULL,
  bsn_external varchar(64) NOT NULL,
  bsn_internal varchar(64) NOT NULL,
  payload varchar(2048) NOT NULL,
  version_cims varchar(10) NOT NULL,
  version_vcbe varchar(10) not null,
  created_at   timestamp(0) default current_timestamp 
);

ALTER TABLE ONLY public.vaccinatie_event
    ADD CONSTRAINT vaccinatie_event_pkey PRIMARY KEY (id);


ALTER TABLE public.vaccinatie_event OWNER TO vcbe_dba;

-- Make sure the user only can add and read. Deletion and updating could change the integrity of the data
REVOKE ALL ON TABLE public.vaccinatie_event FROM cims_ro;
GRANT SELECT ON TABLE public.vaccinatie_event TO minous;

CREATE INDEX idx_vaccinatie_event_bsn_external ON public.vaccinatie_event (bsn_external);
CREATE INDEX idx_vaccinatie_event_bsn_internal ON public.vaccinatie_event (bsn_internal);
-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_info (
  datetime_refresh timestamp(0) not null,
  duration_refresh integer not null,
  refresh_type varchar(1) not null,
  result  varchar(1) not null
);

ALTER TABLE public.vaccinatie_event_info OWNER TO vcbe_dba;


-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_logging (
  created_date date not null,
  bsn_external varchar(64) not null,
  channel varchar(10) not null default 'cims',
  created_at timestamp(0) not null
) PARTITION BY RANGE (created_date);

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

CREATE TABLE vaccinatie_event_logging_20210420 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-20') TO ('2021-04-21');

CREATE TABLE vaccinatie_event_logging_20210421 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-21') TO ('2021-04-22');

CREATE TABLE vaccinatie_event_logging_20210422 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-22') TO ('2021-04-23');

CREATE TABLE vaccinatie_event_logging_20210423 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-23') TO ('2021-04-24');

CREATE TABLE vaccinatie_event_logging_20210424 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-24') TO ('2021-04-25');

CREATE TABLE vaccinatie_event_logging_20210425 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-25') TO ('2021-04-26');

CREATE TABLE vaccinatie_event_logging_20210426 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-26') TO ('2021-04-27');

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

REVOKE ALL ON TABLE public.vaccinatie_event_logging FROM cims_ro;
GRANT INSERT, SELECT ON TABLE public.vaccinatie_event_logging TO minous;
GRANT SELECT ON TABLE public.vaccinatie_event_logging TO cims_ro;


-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_request (
  created_date date not null,
  bsn_external varchar(64) not null,
  channel varchar(10) not null default 'cims',
  created_at timestamp(0) not null
) PARTITION BY RANGE (created_date);

ALTER TABLE public.vaccinatie_event_request OWNER TO vcbe_dba;

CREATE TABLE vaccinatie_event_request_20210420 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-20') TO ('2021-04-21');

CREATE TABLE vaccinatie_event_request_20210421 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-21') TO ('2021-04-22');

CREATE TABLE vaccinatie_event_request_20210422 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-22') TO ('2021-04-23');

CREATE TABLE vaccinatie_event_request_20210423 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-23') TO ('2021-04-24');

CREATE TABLE vaccinatie_event_request_20210424 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-24') TO ('2021-04-25');

CREATE TABLE vaccinatie_event_request_20210425 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-25') TO ('2021-04-26');

CREATE TABLE vaccinatie_event_request_20210426 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-26') TO ('2021-04-27');

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

REVOKE ALL ON TABLE public.vaccinatie_event_request FROM cims_ro;
GRANT INSERT, SELECT ON TABLE public.vaccinatie_event_request TO minous;
GRANT SELECT ON TABLE public.vaccinatie_event_request TO cims_ro;


CREATE OR REPLACE FUNCTION f_manage_partitions_day( p_schema text , p_tablename text , p_number_of_days integer)
 RETURNS integer
 LANGUAGE plpgsql SECURiTY DEFINER
AS $function$
  DECLARE
  lt_query text;
  ln_query_count integer;
  ln_count integer;

  lt_new_table text ;
  lt_like_table text ;

  ls_year_from varchar(4);
  ls_month_from varchar(2);
  ls_day_from  varchar(2);

  ls_year_to varchar(4);
  ls_month_to varchar(2);
  ls_day_to  varchar(2);

  ln_oldest_partition integer;
  ln_newest_partition integer;
  ln_current_partition integer;

  part_tables cursor for
       select right(table_name , 8 ) as part_name from information_schema.tables
        where table_schema = p_schema
          and table_name like p_tablename||'_%'
          and  right(table_name, 8)::integer < ln_oldest_partition;
/*
Type : Function
Name : f_manage_partitions_day
Paramaters :
- Schema    : 'cdrs'
- Tablename : 'cdrs_data'
- Number_of_days : 7
Return type : Integer
- 0 : okay
> 0 : Error
Description.
Parameters are checked.
-- Not empty                   ==> Error
-- If exists, if not           ==> Error
   --- Schema
   --- Table in schema
   --- Table is Partitioned
If checks are okay.
CONSTANTS:
Check the partitions.
--- Determine the oldest partition
--- Remove all partions, that are older dan oldest partition
--- Add the missing partions to the table until newest partition.
Example:
    CURRENT_DATE : 20210414
    Partitions in the database
    _20210405
    _20210406
    _20210407
    _20210408
    _20210409
    _20210410
    _20210411
    _20210412
    _20210413
    _20210414
    _20210415
    _20210416
    _20210417
    _20210418
    _20210419
    _20210420

    Partions older then 20210407 are removed: 20210405 20210406
    Partions are created until 20210421
Return 0

*/

BEGIN
  /*
  check if the paramters that are past are correctly
  */
  select count(*) into ln_query_count
    from information_schema.tables
   where table_schema = p_schema
     and table_name = p_tablename;

  if ln_query_count = 0 then
    return 2;
  end if;

  /* determine the oldest , newest and current partition */
  select date_part( 'year', current_date - p_number_of_days )::text
         || right('0'|| date_part ('month' , current_date - p_number_of_days)::text,2)
         || right('0'||date_part('day', current_date - p_number_of_days)::text,2)::integer
    into ln_oldest_partition ;

  select date_part( 'year', current_date + p_number_of_days )::text
         || right('0'|| date_part ('month' , current_date + p_number_of_days)::text,2)
         || right('0'||date_part('day', current_date + p_number_of_days)::text,2)
    into ln_newest_partition ;

  ln_query_count = 0;
  lt_query='Leeg';

  /*
    Start with removing the old partitions
  */
  raise notice 'Start checking to delete partitions - % ' , ln_oldest_partition ;

  for r_rec in part_tables
  loop
    lt_query = 'drop table ' || p_schema || '.' || p_tablename ||'_'|| r_rec.part_name || ';' ;
    raise notice 'Query % ', lt_query ;

    execute lt_query;
  end loop;

  /*
     Create the partitions that are not there
  */

  raise notice 'Manage the new partitions';
  ln_count := 0;

  while ln_count  <= p_number_of_days
  loop
    select date_part( 'year', current_date + ln_count )::text
           || right('0'|| date_part ('month' , current_date + ln_count )::text,2)
           || right('0'||date_part('day', current_date + ln_count )::text,2)
      into ln_current_partition ;

    select date_part( 'year', current_date + ln_count )::text
           , right('0'|| date_part ('month' , current_date + ln_count )::text,2)
           , right('0'||date_part('day', current_date + ln_count )::text,2)
      into ls_year_from , ls_month_from , ls_day_from ;

    ln_count := ln_count + 1;

    select date_part( 'year', current_date + ln_count )::text
           , right('0'|| date_part ('month' , current_date + ln_count )::text,2)
           , right('0'||date_part('day', current_date + ln_count )::text,2)
      into ls_year_to , ls_month_to , ls_day_to ;

    lt_new_table := p_tablename||'_'||ln_current_partition;

    raise notice 'Partition : % - % ', ln_current_partition , lt_new_table ;

    lt_query='select count(*) from information_schema.tables where table_schema = ''' || p_schema || ''' and table_name = ''' || lt_new_table ||  '''' ;

    execute lt_query into ln_query_count;
    raise notice 'Query % - % ', ln_query_count , lt_query;

    if ln_query_count = 0 then
      raise notice 'Creating';

      lt_query = 'Create table ' || p_schema || '.' || lt_new_table || ' PARTITION OF ' ||  p_schema || '.' || p_tablename;
      lt_query = lt_query || ' FOR VALUES FROM (''' || ls_year_from || '-' || ls_month_from || '-' || ls_day_from || ''') ';
      lt_query = lt_query || ' TO (''' || ls_year_to || '-' || ls_month_to || '-'  || ls_day_to || ''') ';

      raise notice 'Query : % '  , lt_query;
      execute lt_query ;
    end if;

  end loop;

  return 0;

end;
$function$
;

select f_manage_partitions_day( 'public' , 'vaccinatie_event_request'  , 7 );
select f_manage_partitions_day( 'public' , 'vaccinatie_event_logging'  , 7 );
-- Datum : 28-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

ALTER TABLE public.vaccinatie_event_logging 
ADD column events integer not null;
-- Datum : 29-04-2021
-- Waarom : Setup vcbe_db 
-- Wie   : Rob

ALTER TABLE public.vaccinatie_event
ADD COLUMN iv VARCHAR(32) NOT NULL;
-- Wie : Rob
-- Datum : 03-05-2021
-- Waarom : CIMS_RW

do $$
<<first_block>>
declare
  ln_count integer := 0;
begin
   -- Check if user exists

   select count(*)
   into ln_count
   from pg_user
   where usename = 'cims_rw';

   if ln_count = 0 then
     CREATE user cims_rw password 'hpD2r3B9tmXqZ67wHvxT';
   end if;

end first_block $$;


GRANT SELECT, DELETE ON TABLE public.vaccinatie_event_logging TO cims_rw;


-- Datum : 03-05-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

ALTER TABLE public.vaccinatie_event_info
ADD column datetime_finished timestamp(0);
-- Datum : 03-05-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

-- CREATE EXTENSION IF NOT EXISTS oracle_fdw;

-- create server ora_cims foreign data wrapper oracle_fdw options (dbserver 'rivm-cvdb-l01t.rivm.scc-campus.nl/OCIMS );

-- create user mapping for postgres server ora_cims options (user 'VCBE', password 'cdl4FkZyBDUaHunANAtu');

create schema ora_vcbe;

-- import foreign schema "VCBE" from server ora_cims into ora_vcbe;


-- Datum : 03-05-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

grant connect on database vcbe_db to cims_rw;
grant connect on database vcbe_db to minous;

-- Datum : 03-05-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE OR REPLACE FUNCTION f_update_vaccinatie_events(p_type char(1) )
  RETURNS integer
  LANGUAGE plpgsql
AS $function$
declare
  ln_count integer;
  lt_last_update timestamp;
  lt_finished timestamp;
  lt_current_update timestamp;
  ln_duration integer;
  lt_version char(10);
BEGIN
  /*
     Type : F / I

     Indien F : Volledige tabel refresh vanuit cims

     Indien I : Incremental refesh vanaf de laaste succesvolle run

     Zaken die we kunnen proberen
     - Oracle Foreign_table ==> PG Materialized view

  */

  lt_version := '1.0' ;

  if p_type != 'F' and p_type != 'I'
  then
    raise notice ' Verkeerde type ' ;
    return 9;

  end if;

  if p_type = 'I' then
    raise notice 'Increemental ' ;
    raise notice ' Start time : %' , clock_timestamp();

    select coalesce(max(datetime_refresh), '01-01-2021 00:00:00' )
      into lt_last_update
      from vaccinatie_event_info
     where result = 'T' ;

    if lt_last_update is null
    then
      lt_last_update = '2021-01-01 00:00:00' ;
    end if;

    raise notice ' Last update time : %' , lt_last_update;
    select clock_timestamp() into lt_current_update;

    ---- Do update / insert

    insert into public.vaccinatie_event ( id , bsn_external , bsn_internal , payload , iv , version_cims, version_vcbe , created_at )
           select id, bsnextern, bsnintern , payload , initialisatie_vector   , "version" , '1.0' , clock_timestamp()
             from ora_vcbe.vaccinatie_event where created_at >= lt_last_update
    ON CONFLICT (id)
    DO
       UPDATE SET payload      = excluded.payload
                , iv           = excluded.iv
                , version_cims = excluded.version_cims
                , version_vcbe = lt_version;

    select date_part ( 'minutes' , clock_timestamp() - lt_current_update ) into ln_duration;

    select clock_timestamp() into lt_finished;

    insert into vaccinatie_event_info (datetime_refresh, datetime_finished , duration_refresh , refresh_type , result )
    values ( lt_current_update , lt_finished, ln_duration , p_type , 'T' );

    raise notice ' Finished time : %' , clock_timestamp();

  else
    raise notice ' Full' ;
    lt_last_update = '2021-01-01 00:00:00' ;
    select clock_timestamp() into lt_current_update;
    raise notice ' Start time : %' , clock_timestamp();

    truncate vaccinatie_event;

    insert into public.vaccinatie_event ( id , bsn_external , bsn_internal , payload , iv , version_cims, version_vcbe , created_at )
           select id, bsnextern, bsnintern , payload , initialisatie_vector   , "version" , '1.0' , clock_timestamp()
             from ora_vcbe.vaccinatie_event ;

    select date_part ( 'minutes' , clock_timestamp() - lt_current_update ) into ln_duration;

    select clock_timestamp() into lt_finished;

    insert into vaccinatie_event_info (datetime_refresh, datetime_finished , duration_refresh , refresh_type , result )
    values ( lt_current_update , lt_finished, ln_duration , p_type , 'T' );

    raise notice ' Finished  time : %' , clock_timestamp();
  end if;

  return 0;
end;
$function$
;

ALTER TABLE public.vaccinatie_event_logging ADD COLUMN nen_role CHAR(2);
