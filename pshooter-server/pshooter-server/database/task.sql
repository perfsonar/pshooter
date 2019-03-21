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
                                DEFAULT gen_random_uuid(),


        	-- When this record was added
        	added		TIMESTAMP WITH TIME ZONE
        			NOT NULL
        			DEFAULT now(),

        	-- Specifcation, as provided by the client
        	spec		JSON
        			NOT NULL,


        	-- Requester hints, as provided by the API server
        	hints		JSON
        			NOT NULL,

        	-- Current state
        	state		INTEGER
        			REFERENCES task_state(id)
        			DEFAULT task_state_pending(),

        	-- Path, as supplied or traced (provided by the service)
        	path		JSON,

        	-- Time when we think the tests will be finished
        	eta		TIMESTAMP WITH TIME ZONE,

        	-- Result set, as provided by us
        	result		JSON,

        	-- Diagnostics
        	diags		TEXT,

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

    -- If we're being updated into a finished state, set the ETA to now.
    IF TG_OP = 'UPDATE'
        AND EXISTS (SELECT * FROM task_state WHERE id = NEW.state AND finished)
    THEN
        NEW.eta = now();
	NOTIFY task_finished;
    END IF;

    -- Fill in the full version of the JSON
    NEW.fullrec := json_build_object(
	'diags', NEW.diags,
	'eta', timestamp_with_time_zone_to_iso8601(NEW.eta),
	'hints', NEW.hints,
	'path', NEW.path,
	'result', NEW.result,
        'spec', NEW.spec,
	'state-display', (SELECT display FROM task_state where task_state.id = NEW.state),
	'state', (SELECT enum FROM task_state where task_state.id = NEW.state)
	);


    NOTIFY task_update;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER task_insert_update BEFORE INSERT OR UPDATE ON task
    FOR EACH ROW EXECUTE PROCEDURE task_insert_update();



---
--- Maintenance
---

DO $$ BEGIN PERFORM drop_function_all('task_reset'); END $$;

CREATE OR REPLACE FUNCTION task_reset()
RETURNS VOID
AS $$
BEGIN

    -- Reset all running tasks to pending so they get picked up and
    -- run again.

    UPDATE task
    SET
        state = task_state_pending(),
        eta = NULL
    WHERE
        state IN (SELECT id FROM task_state WHERE running);

END;
$$ LANGUAGE plpgsql;



DO $$ BEGIN PERFORM drop_function_all('task_maintain'); END $$;

CREATE OR REPLACE FUNCTION task_maintain()
RETURNS VOID
AS $$
DECLARE
    older_than TIMESTAMP WITH TIME ZONE;
BEGIN

    -- Get rid of old tasks

    SELECT INTO older_than normalized_now() - keep
    FROM configurables;

    DELETE FROM task WHERE eta < older_than;

END;
$$ LANGUAGE plpgsql;


--
-- A view for development convenience
--

DROP VIEW IF EXISTS task_summary;

CREATE OR REPLACE VIEW task_summary AS
SELECT
    task.id,
    task_state.enum AS state,
    task.added,
    task.eta
FROM
    task
    JOIN task_state on task_state.id = task.state
ORDER BY added
;



---
--- API
---

DO $$ BEGIN PERFORM drop_function_all('api_task_post'); END $$;

CREATE OR REPLACE FUNCTION api_task_post(spec JSON, hints JSON)
RETURNS UUID
AS $$
DECLARE
    inserted RECORD;
BEGIN

    WITH inserted_row AS (
        INSERT INTO TASK (spec, hints) VALUES (spec, hints)
        RETURNING *
    ) SELECT INTO inserted * FROM inserted_row;

    RETURN inserted.uuid;

END;
$$ LANGUAGE plpgsql;



DO $$ BEGIN PERFORM drop_function_all('api_task_cancel'); END $$;

CREATE OR REPLACE FUNCTION api_task_cancel(task UUID)
RETURNS BOOLEAN
AS $$
BEGIN
    RAISE EXCEPTION 'Not implemented yet.';
END;
$$ LANGUAGE plpgsql;
