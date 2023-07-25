module log {

  type DatasetBase {
    action: str;
    required target: dataset::DatasetBase;
    required updated: datetime;
  }

}