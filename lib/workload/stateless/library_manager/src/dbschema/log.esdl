module log {

  scalar type Action extending enum<'INSERT', 'UPDATE', 'DELETE'>;

  type Metadata {
    required action: Action;
    required updatedTime: datetime;
    detail: json;
    object: metadata::MetadataLoggable {
      on target delete allow;
    };
  }

}