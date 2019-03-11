--
-- Maintenance
--

CREATE OR REPLACE FUNCTION maintain()
RETURNS VOID
AS $$
BEGIN
    PERFORM task_maintain();
END;
$$ LANGUAGE plpgsql;
