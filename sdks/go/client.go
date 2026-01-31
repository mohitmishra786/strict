package strict

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type SignalType string

const (
	Analog  SignalType = "analog"
	Digital SignalType = "digital"
	Hybrid  SignalType = "hybrid"
)

type ProcessorType string

const (
	Cloud  ProcessorType = "cloud"
	Local  ProcessorType = "local"
	HybridProc ProcessorType = "hybrid"
)

type ProcessingRequest struct {
	InputData      string        `json:"input_data"`
	InputTokens    int           `json:"input_tokens"`
	ProcessorType  ProcessorType `json:"processor_type,omitempty"`
	TimeoutSeconds float64       `json:"timeout_seconds,omitempty"`
}

type ValidationResult struct {
	Status    string   `json:"status"`
	IsValid   bool     `json:"is_valid"`
	InputHash string   `json:"input_hash"`
	Errors    []string `json:"errors"`
}

type OutputSchema struct {
	Result            interface{}      `json:"result"`
	Validation        ValidationResult `json:"validation"`
	ProcessorUsed     ProcessorType    `json:"processor_used"`
	ProcessingTimeMs  float64          `json:"processing_time_ms"`
	RetriesAttempted  int              `json:"retries_attempted"`
}

type Client struct {
	BaseURL    string
	APIKey     string
	httpClient *http.Client
}

func NewClient(baseURL, apiKey string) *Client {
	return &Client{
		BaseURL: baseURL,
		APIKey:  apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) ProcessRequest(ctx context.Context, req ProcessingRequest) (*OutputSchema, error) {
	data, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	// Use request timeout if specified, otherwise rely on context
	requestCtx := ctx
	if req.TimeoutSeconds > 0 {
		var cancel context.CancelFunc
		requestCtx, cancel = context.WithTimeout(ctx, time.Duration(req.TimeoutSeconds*float64(time.Second)))
		defer cancel()
	}

	httpReq, err := http.NewRequestWithContext(requestCtx, "POST", c.BaseURL+"/process/request", bytes.NewBuffer(data))
	if err != nil {
		return nil, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.APIKey != "" {
		httpReq.Header.Set("X-API-Key", c.APIKey)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var output OutputSchema
	if err := json.NewDecoder(resp.Body).Decode(&output); err != nil {
		return nil, err
	}

	return &output, nil
}
