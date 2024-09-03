package fmannotator

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/fmannotator/schema/orcabus_workflowmanager/workflowrunstatechange"
	"io"
	"log/slog"
	"net/http"
	"net/url"
)

// A JsonPatch used to update FM records.
type JsonPatch struct {
	Op    string `json:"op"`
	Path  string `json:"path"`
	Value string `json:"value,omitempty"`
}

// The PatchList for updating records.
type PatchList []JsonPatch

// MarshallPortalRunId MarshallPatch Convert an event into a JSON patch using the portalRunId.
func MarshallPortalRunId(event *workflowrunstatechange.Event) ([]byte, error) {
	return json.Marshal(PatchList{JsonPatch{
		"add",
		"/portalRunId",
		event.Detail.PortalRunId,
	}})
}

// The ApiClient which is used to send requests to filemanager.
type ApiClient struct {
	Client  *http.Client
	Request *http.Request
}

// NewApiClient Create a new ApiClient.
func NewApiClient(config *Config, body io.Reader) (*ApiClient, error) {
	req, err := http.NewRequest("GET", config.FileManagerEndpoint, body)
	if err != nil {
		return nil, err
	}

	return &ApiClient{
		Client:  &http.Client{},
		Request: req,
	}, nil
}

// WithMethod Set the method for the request.
func (c *ApiClient) WithMethod(method string) *ApiClient {
	c.Request.Method = method
	return c
}

// WithHeader Add a header to the request
func (c *ApiClient) WithHeader(key string, value string) *ApiClient {
	c.Request.Header.Add(key, value)
	return c
}

// WithS3Endpoint Set the endpoint to query S3 records.
func (c *ApiClient) WithS3Endpoint() *ApiClient {
	c.Request.URL.Path = "/api/v1/s3"
	return c
}

// WithQuery Set the query parameters.
func (c *ApiClient) WithQuery(query url.Values) *ApiClient {
	c.Request.URL.RawQuery = query.Encode()
	return c
}

// Do the request returning the response body and status code.
func (c *ApiClient) Do() ([]byte, int, error) {
	slog.Debug(fmt.Sprintf("sending request to %v", c.Request.URL.String()))

	resp, err := c.Client.Do(c.Request)
	if err != nil {
		return []byte{}, 0, err
	}
	defer func() {
		err = errors.Join(resp.Body.Close())
	}()

	status := resp.StatusCode
	body, err := io.ReadAll(resp.Body)
	return body, status, err
}
