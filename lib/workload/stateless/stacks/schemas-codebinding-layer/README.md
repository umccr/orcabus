# schemas-codebinding-layer

This stack creates `PythonLayerVersion` with defined schemas codebinding modules in the layers folder for schemas code binding across stacks.

### How to apply in your stack
For most of circumstance, the functions who need schema codebinding locate in the stateless stack collection. We can import directly thorugh the `this.SchemasCodeBindingStack`, see example:
```
this.BclConvertManagerStack = new BclConvertManagerStack(scope, 'BclConvertManagerStack', {
      ...this.createTemplateProps(env, 'BclConvertManagerStack'),
      ...statelessConfiguration.BclConvertManagerStackProps,
      ...{ schemasCodeBindingLambdaLayerArn: this.SchemasCodeBindingStack.lambdaLayerVersionArn },
    });
```
And then find the layer we need through the `LambdaLayerArn`:
```
const SchemasCodeBindingLambdaLayer = PythonLayerVersion.fromLayerVersionArn(
      this,
      'SchemasCodeBindingLambdaLayer',
      props.schemasCodeBindingLambdaLayerArn
    );
```
