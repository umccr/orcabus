# Stacky McStackFace MetadataManager Dynamo Db

The dynamo db service that stores the hacky metadata manager

We have various id types

* instrument_run_id
  * Contains the instrument run id
  * The samplesheet as a json
  * The instrument lanes 

* instrument lane
  * The instrument run id, plus the lane number
  * The library run ids in this lane

* library id
  * A library id with metadata

* library lane id
  * A library lane id that connects an instrument lane to a library id
  * There may be multiple library lanes for a library id

* 


