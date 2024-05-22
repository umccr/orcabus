# Shared Lambda Layer

This stack creates shared Lambda layers for function used acrross orcabus serverless service.

## Layers List

- ExecutionServiceCodeBindingLayer

## Example

Example of defined schemas codebinding modules in the layers folder for schemas code binding across stacks.

### schemas-codebinding-layer

#### How to apply in your stack

For most of circumstance, the functions who need schema codebinding locate in the stateless stack collection. So We can import directly thorugh the `this.SharedLayersStack`, see example:

```typescript
this.bclConvertManagerStack = new BclConvertManagerStack(scope, 'BclConvertManagerStack', {
      ...this.createTemplateProps(env, 'BclConvertManagerStack'),
      ...statelessConfiguration.BclConvertManagerStackProps,
      ...{
        schemasCodeBindingLambdaLayerArn: this.sharedLayersStack.executionServiceCodeBindingLayer,
      },
    });
```

And then find the layer we need through the `StackProps`:

```typescript
new PythonFunction(this, 'EventTranslator', {
      entry: path.join(__dirname, '../translator_service'),
      layers: [props.schemasCodeBindingLambdaLayerObj],
      ...
    });
```
