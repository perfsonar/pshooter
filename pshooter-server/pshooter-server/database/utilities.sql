--
-- UTILITIES
-- 
--

-- ----------------------------------------------------------------------------

--
-- CONVERSIONS
--

-- Most of these functions take a TEXT value and attempt to convert it
-- into the return type.  If the 'picky' argument is TRUE, the
-- function will raise an exception if the conversion fails, otherwise
-- it will return NULL.


DO $$ BEGIN PERFORM drop_function_all('timestamp_with_time_zone_to_iso8601'); END $$;

CREATE OR REPLACE FUNCTION 
timestamp_with_time_zone_to_iso8601(
	value TIMESTAMP WITH TIME ZONE
)
RETURNS TEXT
AS $$
DECLARE
        hours INTEGER;
        minutes INTEGER;
	converted TEXT;
BEGIN

    IF value IS NULL
    THEN
        RETURN NULL;
    END IF;

    converted := to_char(value, 'YYYY-MM-DD"T"HH24:MI:SS');

    hours := extract(timezone_hour from value);
    IF hours <> 0
    THEN
        converted := converted || trim(to_char(hours, 'MIPL'));
        converted := converted || trim(to_char(abs(hours), '00'));
        minutes := extract(timezone_minutes from value);
        IF MINUTES <> 0
        THEN
            converted := converted || ':' || trim(to_char(minutes, '00'));
        END IF;
    ELSE
        converted := converted || 'Z';
    END IF;

    RETURN converted;
END;
$$ LANGUAGE plpgsql;



-- ----------------------------------------------------------------------------

--
-- DATE AND TIME
--


-- Truncate a timestamp to our scheduling increment (seconds)

DO $$ BEGIN PERFORM drop_function_all('normalized_time'); END $$;

CREATE OR REPLACE FUNCTION normalized_time(value TIMESTAMP WITH TIME ZONE)
RETURNS TIMESTAMP WITH TIME ZONE
AS $$
BEGIN
	RETURN date_trunc('seconds', value);
END;
$$LANGUAGE plpgsql;


-- Return the normalized current (transaction start) time

DO $$ BEGIN PERFORM drop_function_all('normalized_now'); END $$;

CREATE OR REPLACE FUNCTION normalized_now()
RETURNS TIMESTAMP WITH TIME ZONE
AS $$
BEGIN
	RETURN normalized_time(now());
END;
$$LANGUAGE plpgsql;


-- Return the normalized wall clock time

DO $$ BEGIN PERFORM drop_function_all('normalized_wall_clock'); END $$;

CREATE OR REPLACE FUNCTION normalized_wall_clock()
RETURNS TIMESTAMP WITH TIME ZONE
AS $$
BEGIN
	RETURN normalized_time(clock_timestamp());
END;
$$LANGUAGE plpgsql;



-- ----------------------------------------------------------------------------

--
-- DEBUGGING TOOLS
--

DROP VIEW IF EXISTS queries;
CREATE OR REPLACE VIEW queries
AS
    SELECT
        application_name,
        state,
        CASE state
            WHEN 'active' THEN (now() - query_start)::TEXT
            ELSE 'FINISHED'
            END
            AS run_time,
            regexp_replace(query, '[ \t]+', ' ', 'g') AS query
FROM pg_stat_activity
ORDER BY run_time desc
;
