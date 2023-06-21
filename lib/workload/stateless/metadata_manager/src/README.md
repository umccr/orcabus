
# Development

### Install
Create a virtual environment and install the `requirements-dev.txt`

1. Make virtual environment 
   
   `python -mvenv .venv`
2. Activate the environment

   `source .venv/bin/activate`
3. Install the dependency

   `make install`


### Testing

Go this directory
`cd lib/workload/stateless/metadata_manager/src`

And use the makefile to start testing
`make test`
