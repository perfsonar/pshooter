--
-- Task State
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

    t_name := 'task_state';

    t_version := table_version_find(t_name);
    t_version_old := t_version;


    --
    -- Upgrade Blocks
    --

    -- Version 0 (nonexistant) to version 1
    IF t_version = 0
    THEN

        CREATE TABLE task_state (

        	-- Row identifier
        	id		INTEGER
        			PRIMARY KEY,

        	-- Display name
        	display		TEXT
        			UNIQUE NOT NULL,

        	-- Enumeration for use by programs
        	enum		TEXT
        			UNIQUE NOT NULL,

        	-- True if the state represents a finished state
        	finished	BOOLEAN
        			NOT NULL
        );

	t_version := t_version + 1;

    END IF;

    -- -- Version 1 to version 2
    -- IF t_version = 1
    -- THEN

    --     t_version := t_version + 1;
    -- END IF;


    --
    -- Cleanup
    --

    PERFORM table_version_set(t_name, t_version, t_version_old);

END;
$$ LANGUAGE plpgsql;



--
-- Functions that encapsulate the numeric values for each state
--

-- NOTE: These use ALTER FUNCTION to set the IMMUTABLE attribute
-- because in some cases, replacement doesn't set it properly.

-- Task is waiting to execute
CREATE OR REPLACE FUNCTION task_state_pending()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 1;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_pending() IMMUTABLE;


-- Task is being prepared for execution
CREATE OR REPLACE FUNCTION task_state_prep()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 2;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_pending() IMMUTABLE;


-- Initial traceroute is being done (optional step_
CREATE OR REPLACE FUNCTION task_state_trace()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 3;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_trace() IMMUTABLE;

-- Task is being executed
CREATE OR REPLACE FUNCTION task_state_running()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 4;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_running() IMMUTABLE;

-- Post-task HTTP callback
CREATE OR REPLACE FUNCTION task_state_callback()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 5;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_callback() IMMUTABLE;

-- Task finished successfully
CREATE OR REPLACE FUNCTION task_state_finished()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 6;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_finished() IMMUTABLE;


-- Task ran but was not a success
CREATE OR REPLACE FUNCTION task_state_failed()
RETURNS INTEGER
AS $$
BEGIN
	RETURN 7;
END;
$$ LANGUAGE plpgsql;
ALTER FUNCTION task_state_failed() IMMUTABLE;




DROP TRIGGER IF EXISTS task_state_alter ON task_state CASCADE;

CREATE OR REPLACE FUNCTION task_state_alter()
RETURNS TRIGGER
AS $$
BEGIN
	RAISE EXCEPTION 'This table may not be altered';
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

 CREATE TRIGGER task_state_alter
BEFORE INSERT OR UPDATE OR DELETE
ON task_state
       FOR EACH ROW EXECUTE PROCEDURE task_state_alter();



-- Do this after trigger creation and with a DISABLE/ENABLE in case
-- the table was previously populated.

ALTER TABLE task_state DISABLE TRIGGER task_state_alter;
INSERT INTO task_state (id, display, enum, finished)
VALUES
    (task_state_pending(),   'Pending',     'pending',   FALSE),
    (task_state_prep(),      'Preparing',   'prep',      FALSE),
    (task_state_trace(),     'Trace',       'trace',     FALSE),
    (task_state_running(),   'Running',     'running',   FALSE),
    (task_state_callback(),  'Callback',    'callback',  FALSE),
    (task_state_finished(),  'Finished',    'finished',  TRUE),
    (task_state_failed(),    'Failed',      'failed',    TRUE)
ON CONFLICT (id) DO UPDATE
SET
    display = EXCLUDED.display,
    enum = EXCLUDED.enum,
    finished = EXCLUDED.finished;
ALTER TABLE task_state ENABLE TRIGGER task_state_alter;


-- Determine if a transition between states is valid
DO $$ BEGIN PERFORM drop_function_all('task_state_transition_is_valid'); END $$;

CREATE OR REPLACE FUNCTION task_state_transition_is_valid(
    old INTEGER,
    new INTEGER
)
RETURNS BOOLEAN
AS $$
BEGIN
    -- TODO: This might be worth putting into a table.
    RETURN new = old
           OR   ( old = task_state_pending()
	          AND new IN (task_state_prep(),
			      task_state_failed()) )
           OR   ( old = task_state_prep()
	          AND new IN (task_state_trace(),
			      task_state_running(),
			      task_state_failed()) )
           OR   ( old = task_state_trace()
	          AND new IN (task_state_running(),
			      task_state_failed()) )
           OR ( old = task_state_running()
	        AND new IN (task_state_callback(),
			    task_state_failed()) )
           OR ( old = task_state_callback()
	        AND new IN (task_state_finished(),
			    task_state_failed()) )
           ;
END;
$$ LANGUAGE plpgsql;
