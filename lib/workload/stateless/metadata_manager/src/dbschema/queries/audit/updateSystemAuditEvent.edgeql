# Update a system audit event.
with module audit
update SystemAuditEvent
filter .id = <uuid>$auditDbId
set
{
  actionOutcome := <ActionOutcome>$actionOutcome,
  details :=  <json>$details,
  occurredDateTime := <datetime>$occurredDateTime,
  inProgress := <bool>$inProgress
}
