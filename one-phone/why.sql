WITH eff AS (
  SELECT o.id, o.name, (o.dialer_enabled = true OR EXISTS (SELECT 1 FROM organization_collaborations oc JOIN organizations c2 ON c2.id = oc.collaborator_id WHERE oc.organization_id = o.id AND c2.dialer_enabled_for_collaborations = true)) AS dialer
  FROM organizations o),
lines AS (
  SELECT e.user_id, eff.name, eff.dialer,
    EXISTS (SELECT 1 FROM organization_members m WHERE m.user_id = e.user_id AND m.organization_id = e.organization_id) AS member,
    lower(e.organization_id::text) = ANY($1::text[]) AS listed
  FROM extensions e JOIN eff ON eff.id = e.organization_id WHERE e.user_id IS NOT NULL),
per_user AS (
  SELECT user_id,
    bool_or(member AND NOT dialer) AS no_dialer,
    bool_or(member AND dialer AND NOT listed) AS not_listed,
    array_agg(DISTINCT name) FILTER (WHERE member AND (NOT dialer OR NOT listed)) AS blocking,
    bool_or(member) AS has_line
  FROM lines GROUP BY user_id)
SELECT CASE WHEN NOT has_line THEN 'no usable line' WHEN no_dialer THEN 'blocked: a line in a company WITHOUT the dialer' WHEN not_listed THEN 'blocked: a line in a dialer company NOT in the list' ELSE 'gets one phone' END AS result,
  array_to_string(blocking, ', ') AS companies, count(*)::int AS agents
FROM per_user GROUP BY 1,2 ORDER BY 1, 3 DESC
