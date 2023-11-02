using extension graphql;
module audit {

  # NOTE: TODO How to query deleted library??

  # ActionType definition
  # Ref: http://hl7.org/fhir/audit-event-action
  scalar type ActionType extending enum<'C', 'R', 'U', 'D', 'E'>;

  # ActionOutcome definition
  # Ref: http://hl7.org/fhir/ValueSet/audit-event-outcome
  scalar type ActionOutcome extending enum<'fatal', 'error', 'warning', 'information', 'success'>;

  abstract type AuditEvent {
    required actionCategory: ActionType;
    required actionOutcome: ActionOutcome;

    # a string describing the action but with no details i.e. "Google metadata sync"
    # any details will appear later in the details JSON
    required actionDescription: str;

    # when this audit record is last updated (e.g. completion/failure of an event)
    # Using `rewrite` to re-update this automatically
    required updatedDateTime: datetime {
      rewrite insert, update using (datetime_of_statement())
    }

    # bespoke JSON with details of the event
    details: json;

  }

  type SystemAuditEvent extending AuditEvent {
  }

}
