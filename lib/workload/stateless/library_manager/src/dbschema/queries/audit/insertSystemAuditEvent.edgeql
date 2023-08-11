# Insert a system audit event.
with module audit
insert SystemAuditEvent {
  
  actionCategory := <optional ActionType>$actionCategory ?? ActionType.E,
  actionDescription := <optional str>$actionDescription ?? "",
  actionOutcome := <optional ActionOutcome>$actionOutcome ?? ActionOutcome.success,

  occurredDateTime := <optional datetime>$occurredDateTime ?? datetime_current(),
  details := <optional json>$details ?? {},
  inProgress := <optional bool>$inProgress ?? false

};
