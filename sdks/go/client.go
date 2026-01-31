package strict

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
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
	BaseURL string
	APIKey  string
}

func NewClient(baseURL, apiKey string) *Client {
	return &Client{
		BaseURL: baseURL,
		APIKey:  apiKey,
	}
}

func (c *Client) ProcessRequest(req ProcessingRequest) (*OutputSchema, error) {
	data, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	httpReq, err := http.NewRequest("POST", c.BaseURL+"/process/request", bytes.NewBuffer(data))
	if err != nil {
		return nil, err
	}

	httpReq.Header.Set("Content-Type", "application/json")
	if c.APIKey != "" {
		httpReq.Header.Set("X-API-Key", c.APIKey)
	}

	client := &http.Client{}
	resp, err := client.Do(httpReq)
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
