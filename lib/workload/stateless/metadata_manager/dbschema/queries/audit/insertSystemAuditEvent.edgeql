# Insert a system audit event.
with module audit
insert SystemAuditEvent {
  
  actionCategory := <optional ActionType>$actionCategory ?? ActionType.E,
  actionDescription := <optional str>$actionDescription ?? "",
  actionOutcome := <optional ActionOutcome>$actionOutcome ?? ActionOutcome.success,

  details := <optional json>$details ?? {},

};
