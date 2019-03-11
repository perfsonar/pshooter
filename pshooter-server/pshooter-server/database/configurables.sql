--
-- Table with one row that holds configurable values
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

    t_name := 'configurables';

    t_version := table_version_find(t_name);
    t_version_old := t_version;


    --
    -- Upgrade Blocks
    --

    -- Version 0 (nonexistant) to version 1
    IF t_version = 0
    THEN

        CREATE TABLE configurables (

            -- How long we should keep old data
            keep   		INTERVAL
        			DEFAULT 'P2D',

            -- Maximum runs in parallel
            max_parallel	INTEGER
        			DEFAULT 20
        );

        -- This table gets exactly one row that can only ever be updated.
        INSERT INTO configurables DEFAULT VALUES;

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



DROP TRIGGER IF EXISTS configurables_alter ON configurables CASCADE;
DROP TRIGGER IF EXISTS configurables_truncate ON configurables CASCADE;

CREATE OR REPLACE FUNCTION configurables_noalter()
RETURNS TRIGGER
AS $$
BEGIN
	RAISE EXCEPTION 'This table can only be updated.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER configurables_alter
BEFORE INSERT OR DELETE
ON configurables
FOR EACH ROW
    EXECUTE PROCEDURE configurables_noalter();

CREATE TRIGGER configurables_truncate
BEFORE TRUNCATE
ON configurables
EXECUTE PROCEDURE configurables_noalter();
