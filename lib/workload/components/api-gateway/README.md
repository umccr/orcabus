# ApiGatewayConstruct

Usage example:

```ts
const srmApi = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
const httpApi = srmApi.httpApi;

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
  authorizer: apiGateway.cognitoAdminGroupAuthorizer,
  routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.POST),
});
```
