# ApiGatewayConstruct

Usage example:

```ts
const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
const httpApi = apiGateway.httpApi;

const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiFn);

new HttpRoute(this, 'GetHttpRoute', {
  httpApi: httpApi,
  integration: apiIntegration,
  routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.GET),
});

// To protect the path/method with an admin role within the User Pool Cognito
// More details on ./.../stateful/authorization-stack

new HttpRoute(this, 'PostHttpRoute', {
  httpApi: httpApi,
  integration: apiIntegration,
  authorizer: apiGateway.authStackHttpLambdaAuthorizer,
  routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.POST),
});
```
