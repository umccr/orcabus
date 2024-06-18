# Python Lambda Layer Construct

This construct is useful if you have packages embedded into the orcabus that you don't necessarily want to push to PyPi.  

Instead you can install them into a lambda layer and use them in your lambda functions.

## Inputs

* layerName: string;
* layerDirectory: string;
* layerDescription: string;