--
-- Task Table
--

DO $$
DECLARE
    t_name TEXT;            -- Name of the table being worked on
    t_version INTEGER;      -- Current version of the table
    t_version_old INTEGER;  -- Version of the table at the start

BEGIN

    --
    -- Preparation
    --

    t_name := 'task';

    t_version := table_version_find(t_name);
    t_version_old := t_version;


    --
    -- Upgrade Blocks
    --

    -- Version 0 (nonexistant) to version 1
    IF t_version = 0
    THEN

        CREATE TABLE task (

        	-- Row identifier
        	id		BIGSERIAL
        			PRIMARY KEY,

        	-- External-use identifier
        	uuid		UUID
        			UNIQUE
                                NOT NULL,


        	-- Time when we think the tests will be finished
        	added		TIMESTAMP WITH TIME ZONE
        			NOT NULL
        			DEFAULT now(),

        	-- Specifcation, as provided by the client				
        	spec		JSON
        			NOT NULL,

        	-- Result set, as provided by us
        	result		JSON
        			NOT NULL,

        	-- Time when we think the tests will be finished
        	eta		TIMESTAMP WITH TIME ZONE,

        	-- Full record, kept updated by triggers
        	fullrec		JSON
        			NOT NULL
        );


        -- This should be used when someone looks up the external ID.  Bring
        -- the row ID a long so it can be pulled without having to consult the
        -- table.
        CREATE INDEX task_uuid
        ON task(uuid, id);

	t_version := t_version + 1;

    END IF;

    -- Version 1 to version 2
    --IF t_version = 1
    --THEN
    --    ALTER TABLE ...
    --    t_version := t_version + 1;
    --END IF;

    --
    -- Cleanup
    --

    PERFORM table_version_set(t_name, t_version, t_version_old);

END;
$$ LANGUAGE plpgsql;





DROP TRIGGER IF EXISTS task_insert ON task CASCADE;

CREATE OR REPLACE FUNCTION task_insert()
RETURNS TRIGGER
AS $$
BEGIN

    NOTIFY task_new;

    RETURN NEW;

END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_insert AFTER INSERT ON task
    FOR EACH ROW EXECUTE PROCEDURE task_insert();



DROP TRIGGER IF EXISTS task_insert_update ON task CASCADE;

CREATE OR REPLACE FUNCTION task_insert_update()
RETURNS TRIGGER
AS $$
BEGIN

    -- Fill in the full version of the JSON

    NEW.fullrec := '{}'::JSON;
    NEW.fullrec := jsonb_set(NEW.fullrec, '{spec}', NEW.spec);
    NEW.fullrec := jsonb_set(NEW.fullrec, '{result}', NEW.result);
    NEW.fullrec := jsonb_set(NEW.fullrec, '{eta}', NEW.result,
            to_jsonb(timestamp_with_time_zone_to_iso8601(NEW.eta)));

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_insert_update AFTER INSERT OR UPDATE ON task
    FOR EACH ROW EXECUTE PROCEDURE task_insert_update();





---
--- Maintenance
---

CREATE OR REPLACE FUNCTION task_purge()
RETURNS VOID
AS $$
DECLARE
    older_than TIMESTAMP WITH TIME ZONE;
BEGIN

    SELECT INTO older_than normalized_now() - keep
    FROM configurables;

    -- Get rid of tasks that no longer have runs and can be considered
    -- completed.

    DELETE FROM task
    WHERE
        NOT EXISTS (SELECT * FROM run where run.task = task.id)
        -- The first of these will be the latest known time.
        AND COALESCE(until, start, added) < older_than
        AND (
            -- Complete based on runs
            (max_runs IS NOT NULL AND runs >= max_runs)
            -- One-shot
            OR repeat IS NULL
            -- Until time has passed
            OR until < older_than
            )
    ;

END;
$$ LANGUAGE plpgsql;



-- Maintenance that happens four times a minute.

CREATE OR REPLACE FUNCTION task_maint_fifteen()
RETURNS VOID
AS $$
BEGIN
    PERFORM task_purge();
END;
$$ LANGUAGE plpgsql;



---
--- API
---


-- Put a task on the timeline and return its UUID

DO $$ BEGIN PERFORM drop_function_all('api_task_post'); END $$;

CREATE OR REPLACE FUNCTION api_task_post(
    task_package JSONB,
    participant_list TEXT[],
    hints JSONB,
    limits_passed JSON = '[]',
    participant INTEGER DEFAULT 0,
    task_uuid UUID = NULL,
    enabled BOOLEAN = TRUE,
    diags TEXT = '(None)'
)
RETURNS UUID
AS $$
DECLARE
    inserted RECORD;
BEGIN

   IF EXISTS (SELECT * FROM task WHERE uuid = task_uuid)
   THEN
       RAISE EXCEPTION 'Task already exists.  All participants must be on separate systems.';
   END IF;

   WITH inserted_row AS (
        INSERT INTO task(json, participants, limits_passed, participant, uuid, hints, enabled, diags)
        VALUES (task_package, array_to_json(participant_list), limits_passed, participant, task_uuid, hints, enabled, diags)
        RETURNING *
    ) SELECT INTO inserted * from inserted_row;

    RETURN inserted.uuid;

END;
$$ LANGUAGE plpgsql;



-- This function enables a task by its UUID.  This is used by the REST
-- API to keep the scheduler from trying to ask the other participants
-- for runtimes when they don't have it yet.  (Other participants'
-- schedulers won't touch their copies because they're not leading.)

DO $$ BEGIN PERFORM drop_function_all('api_task_enable'); END $$;

CREATE OR REPLACE FUNCTION api_task_enable(
    task_uuid UUID        -- UUID of task to enable
)
RETURNS VOID
AS $$
DECLARE
    taskrec RECORD;
BEGIN

    SELECT INTO taskrec * FROM task WHERE uuid = task_uuid;
    IF NOT FOUND
    THEN
        RAISE EXCEPTION 'Task not found while enabling task %', task_uuid;
    END IF;

    IF taskrec.enabled
    THEN
        -- Don't so anything redundant redundant.
        RETURN;
    END IF;

    UPDATE task SET enabled = TRUE WHERE id = taskrec.id;

END;
$$ LANGUAGE plpgsql;


-- This function disables a task and does the corresponding DELETE on
-- the other participants.  The task_url_format argument is the URL of
-- the task with the hostname replaced with %s, which will be filled
-- in with the hostname of each participant.

DO $$ BEGIN PERFORM drop_function_all('api_task_disable'); END $$;

CREATE OR REPLACE FUNCTION api_task_disable(
    task_uuid UUID,       -- UUID of task to disable
    task_url_format TEXT  -- URL template.  See above.
)
RETURNS VOID
AS $$
DECLARE
    taskrec RECORD;
    host TEXT;
    ip INET;
    ip_family INTEGER;
    bind TEXT;
    task_url_append TEXT;
BEGIN

    SELECT INTO taskrec * FROM task WHERE uuid = task_uuid;
    IF NOT FOUND
    THEN
        RAISE EXCEPTION 'Task not found while disabling task %', task_uuid;
    END IF;

    IF NOT taskrec.enabled
    THEN
        -- Don't so anything redundant redundant.
        RETURN;
    END IF;

    UPDATE task SET enabled = FALSE WHERE uuid = task_uuid;

    -- Sling a DELETE at the non-lead participants if there are any
    -- and we're the lead.

    IF taskrec.participant = 0
    THEN

        -- If the task has a lead-bind, use it.
	IF taskrec.json ? 'lead-bind'
	THEN
	    bind := taskrec.json #>> '{"lead-bind"}';
	ELSE
	    bind := NULL;
	END IF;

	-- If this task has a key, append that to the URL.
        IF taskrec.json ? '_key'
	THEN
            task_url_append := '?key=' || uri_encode(taskrec.json ->> '_key');
	ELSE
	    task_url_append := '';
	END IF;

        FOR host IN (SELECT jsonb_array_elements_text(taskrec.participants)
                     FROM task WHERE uuid = task_uuid OFFSET 1)
        LOOP

            -- IPv6 adresses get special treatment
            BEGIN
		IF family(host::INET) = 6
                THEN
                    host := format('[%s]', host);
                END IF;
            EXCEPTION WHEN OTHERS THEN
                NULL;  -- Don't care
            END;

            INSERT INTO http_queue (operation, uri, bind)
                VALUES ('DELETE',
		    format(task_url_format, host) || task_url_append,
		    bind);
        END LOOP;
    END IF;   

END;
$$ LANGUAGE plpgsql;
