package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/kelseyhightower/envconfig"
	"github.com/umccr/orcabus/lib/workload/stateless/stacks/attribute-linker/schema/orcabus_workflowmanager/workflowrunstatechange"
	"io"
	"log/slog"
	"net/http"
	"net/url"
	"strings"
)

type Config struct {
	FileManagerEndpoint string `required:"true" split_words:"true"`
}

type JsonPatch struct {
	Op    string `json:"op"`
	Path  string `json:"path"`
	Value string `json:"value,omitempty"`
}

type PatchList []JsonPatch

func Handler(event workflowrunstatechange.Event) (err error) {
	status := strings.ToUpper(event.Detail.Status)
	if status != "SUCCEEDED" && status != "FAILED" && status != "ABORTED" {
		return nil
	}

	patch, err := json.Marshal(PatchList{JsonPatch{
		"add",
		"/portalRunId",
		event.Detail.PortalRunId,
	}})
	if err != nil {
		return err
	}

	var config Config
	err = envconfig.Process("annotator", &config)
	if err != nil {
		return err
	}
	endpoint, err := url.JoinPath(config.FileManagerEndpoint, "/api/v1/s3")
	if err != nil {
		return err
	}

	client := &http.Client{}

	req, err := http.NewRequest(
		"PATCH",
		endpoint,
		bytes.NewBuffer(patch),
	)
	if err != nil {
		return err
	}

	req.URL.RawQuery = url.Values{
		"key": {fmt.Sprintf("*%v*", event.Detail.PortalRunId)},
	}.Encode()
	req.Header.Add("Content-Type", "application/json")

	slog.Debug(fmt.Sprintf("sending attributes patch %v to %v", patch, req.URL.String()))

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer func() {
		err = errors.Join(resp.Body.Close())
	}()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	if resp.StatusCode != 200 {
		return errors.New(fmt.Sprintf("error annotating attributes with status %v: %v", resp.Status, string(body)))
	}

	slog.Debug(fmt.Sprintf("received response %v with body: %v", resp.StatusCode, body))

	return nil
}

func main() {
	lambda.Start(Handler)
}
