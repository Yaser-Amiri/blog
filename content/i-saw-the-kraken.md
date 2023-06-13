Title: I saw a kraken
Date: 2023-06-13
Category: tech, database, postgresql

PostgreSQL has been one of the first DBMSs I've used, and it has been a reliable choice for me over the past 7 years.
For me, it always has been the statue of "Reliability". I have never personally encountered any bugs in PostgreSQL, this fact
made me think that maybe it's impossible! Maybe you have to be one of the best sailors in the world to be able to see such a rare monster!  

In the spring of 2022, I found a scenario that was causing a bug in [Eveince Platform](https://eveince.com) and no one in our team could find an explanation for it, I thought the Kraken has finally appeared, a bug in PostgreSQL(actually Postgres developer don't call it a bug) which
I couldn't find anything about it anywhere and it was alive on the last version of Postgres.
I started a thread in PostgreSQL's mailing list and talked to the good men of Postgres, they said it's not a bug however it should get documented.
I think I haven't yet, so I decided to write the story, So here I am writing this blog post, hopefully it save a couple of days/hours for someone.

Let's say you have a table called balance, it looks like this (I deleted the primary key, etc to make things more simple):  
```
CREATE TABLE public.balance (
    id uuid NOT NULL,
    version BIGINT DEFAULT '0'::BIGINT NOT NULL,
    "time" TIMESTAMP WITHOUT TIME zone NOT NULL,
    entity_type CHARACTER VARYING(256) NOT NULL,
    entity_id CHARACTER VARYING(256) NOT NULL,
    currency CHARACTER VARYING(64) NOT NULL,
    volume NUMERIC NOT NULL
);
```

There is also a partial multicolumn index:  
```
CREATE UNIQUE INDEX uq_balance_record ON public.balance
USING btree (entity_type, entity_id, "time", currency)
WHERE ("time" > '2021-12-30 23:59:59'::TIMESTAMP WITHOUT TIME zone);
```

It simply says all the records with the same [`entity_type`, `entity_id`, `time`, and `currency`] and
their `time` is greater than `2021-12-30 23:59:59` must be unique and indexed.  
Everything is going well up to this point.

Now let's start writing to this table, a prepared statement would be in order:
```
PREPARE my_insert (uuid, TIMESTAMP, VARCHAR, VARCHAR, VARCHAR, NUMERIC, BIGINT, TIMESTAMP) AS

INSERT INTO balance
(id, time, entity_type, entity_id, currency, volume, version)
VALUES
($1::uuid, $2::TIMESTAMP, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::NUMERIC, $7::BIGINT)
ON CONFLICT (entity_type, entity_id, time, currency)
WHERE TIME > $8::TIMESTAMP
DO UPDATE SET volume = excluded.volume, version = excluded.version
WHERE balance.version < excluded.version;
```

It's an almost simple insert, it basically says if there is a record with the same [`entity_type`, `entity_id`, `time`, and `currency`]
and its `version` is lower than what I want to insert, it should be updated otherwise it's gonna be inserted regularly. We have to put a where clause
after `ON CONFLICT` to satisfy the index's predicate (which was about *the time being at least 2022*) otherwise Postgres would raise an error to
express that it can't find an index for `ON CONFLICT`. The value of this predicate is not strict, it only has to make the predicate "true",
2023, 2033, 2025, all of them are OK (because they're greater than `2021-12-30 23:59:59`)

Now let's use this prepared statement and insert 5 records with the same values, after this transaction, we would have 1 record in the database.

```
BEGIN;
DELETE FROM balance;
EXECUTE my_insert('e063a2aa-53c3-4546-8f90-3955d4b4c23d', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('4f5bb87d-be77-421b-ad86-1cee28187cf6', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('17a5a62e-0736-4eba-8ed7-e76cbd99080a', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('3782cea4-d449-48fd-a56f-cd43c4577230', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('949d18e2-6fca-427a-9aac-a6803ef94b4f', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
COMMIT;

; Result:
BEGIN
DELETE 1
INSERT 0 1
INSERT 0 0
INSERT 0 0
INSERT 0 0
INSERT 0 0
COMMIT
```

It worked. No surprise. BUT if you do the same with one more record (make it 6 records) it'll fail!
`DEALLOCATE` and create the prepared statement again and insert this data:
```
BEGIN;
DELETE FROM balance;
EXECUTE my_insert('e063a2aa-53c3-4546-8f90-3955d4b4c23d', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('4f5bb87d-be77-421b-ad86-1cee28187cf6', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('17a5a62e-0736-4eba-8ed7-e76cbd99080a', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('3782cea4-d449-48fd-a56f-cd43c4577230', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('949d18e2-6fca-427a-9aac-a6803ef94b4f', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
EXECUTE my_insert('3453d9f4-e34a-4e13-b72f-da1112edbe7f', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2, '2025-01-01');
COMMIT;

; Result
BEGIN
DELETE 1
INSERT 0 1
INSERT 0 0
INSERT 0 0
INSERT 0 0
INSERT 0 0
ERROR:  there is no unique or exclusion constraint matching the ON CONFLICT specification
ROLLBACK
```

Weird! Right?! I still don't know what it has to do with number 6!  
Apparently, the root cause of this problem is planning. Hence the predicate value is a parameter, the planer at some point can't be
sure about the value and decides to fail everything. If you make the value a hard-coded one, it would work properly
(the planner can be sure that this X will be the value and it always will hit the index):
```
PREPARE my_insert (uuid, TIMESTAMP, VARCHAR, VARCHAR, VARCHAR, NUMERIC, BIGINT) AS

INSERT INTO balance
(id, time, entity_type, entity_id, currency, volume, version)
VALUES
($1::uuid, $2::TIMESTAMP, $3::VARCHAR, $4::VARCHAR, $5::VARCHAR, $6::NUMERIC, $7::BIGINT)
ON CONFLICT (entity_type, entity_id, time, currency)
WHERE TIME > '2025-01-01'::TIMESTAMP
DO UPDATE SET volume = excluded.volume, version = excluded.version
WHERE balance.version < excluded.version;
```

Then:  
```
BEGIN;
DELETE FROM balance;
EXECUTE my_insert('e063a2aa-53c3-4546-8f90-3955d4b4c23d', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
EXECUTE my_insert('4f5bb87d-be77-421b-ad86-1cee28187cf6', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
EXECUTE my_insert('17a5a62e-0736-4eba-8ed7-e76cbd99080a', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
EXECUTE my_insert('3782cea4-d449-48fd-a56f-cd43c4577230', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
EXECUTE my_insert('949d18e2-6fca-427a-9aac-a6803ef94b4f', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
EXECUTE my_insert('3453d9f4-e34a-4e13-b72f-da1112edbe7f', '2023-01-05T08:00:00', 'A', 'B', 'C', 1, 2);
COMMIT;

; Result
BEGIN
DELETE 1
INSERT 0 1
INSERT 0 0
INSERT 0 0
INSERT 0 0
INSERT 0 0
INSERT 0 0
COMMIT
```

To be honest I still don't understand why this is a "valid behavior" and why isn't considered a bug but
if you want to read more on  PostgreSQL's mailing list, this is the thread:
[Thread](https://www.postgresql.org/message-id/flat/17445-fb74db6348391e85%40postgresql.org)


