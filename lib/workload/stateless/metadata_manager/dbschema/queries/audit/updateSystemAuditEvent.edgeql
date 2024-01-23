# Update a system audit event.
with module audit
update SystemAuditEvent
filter .id = <uuid>$auditDbId
set
{
  actionOutcome := <ActionOutcome>$actionOutcome,
  details :=  <optional json>$details,
}
