module audit {

  # ActionType definition
  # Ref: http://hl7.org/fhir/audit-event-action
  scalar type ActionType extending enum<'C', 'R', 'U', 'D', 'E'>;

  # ActionOutcome definition
  # Ref: http://hl7.org/fhir/ValueSet/audit-event-outcome
  scalar type ActionOutcome extending enum<'fatal', 'error', 'warning', 'information', 'success'>;

  abstract type AuditEvent {
    required actionCategory: ActionType;

    # a string describing the action but with no details i.e. "Google metadata sync"
    # any details will appear later in the details JSON
    required actionDescription: str;

    # when this audit record has been made (should be close to occurredDateTime!)
    required recordedDateTime: datetime {
      default := datetime_current();
      readonly := true;
    }
    required occurredDateTime: datetime {
      default := datetime_current();
    }
    required occurredDuration: duration {
      rewrite insert, update using (
        select __subject__.occurredDateTime - __subject__.recordedDateTime
      )
    }

    # when this audit record is last updated (e.g. completion/failure of an event)
    # Using `rewrite` to re-update this automatically
    required updatedDateTime: datetime {
      rewrite insert, update using (datetime_of_statement())
    }

    required actionOutcome: ActionOutcome;

    # bespoke JSON with details of the event
    details: json;

    # Whether its expected that this audit event will be updated.
    required inProgress: bool;
  }

  type SystemAuditEvent extending AuditEvent {
  }


}
