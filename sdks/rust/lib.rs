use serde::{Deserialize, Serialize};
use reqwest::header::{HeaderMap, HeaderValue};

#[derive(Debug, Serialize, Deserialize)]
pub enum SignalType {
    #[serde(rename = "analog")]
    Analog,
    #[serde(rename = "digital")]
    Digital,
    #[serde(rename = "hybrid")]
    Hybrid,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum ProcessorType {
    #[serde(rename = "cloud")]
    Cloud,
    #[serde(rename = "local")]
    Local,
    #[serde(rename = "hybrid")]
    Hybrid,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessingRequest {
    pub input_data: String,
    pub input_tokens: u32,
    pub processor_type: Option<ProcessorType>,
    pub timeout_seconds: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ValidationResult {
    pub status: String,
    pub is_valid: bool,
    pub input_hash: String,
    pub errors: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OutputSchema {
    pub result: serde_json::Value,
    pub validation: ValidationResult,
    pub processor_used: ProcessorType,
    pub processing_time_ms: f64,
}

pub struct Client {
    base_url: String,
    api_key: Option<String>,
    http_client: reqwest::Client,
}

impl Client {
    pub fn new(base_url: String, api_key: Option<String>) -> Self {
        Self {
            base_url,
            api_key,
            http_client: reqwest::Client::new(),
        }
    }

    pub async fn process_request(&self, request: &ProcessingRequest) -> Result<OutputSchema, reqwest::Error> {
        let mut headers = HeaderMap::new();
        if let Some(ref key) = self.api_key {
            headers.insert("X-API-Key", HeaderValue::from_str(key).unwrap());
        }

        let url = format!("{}/process/request", self.base_url);
        let response = self.http_client
            .post(url)
            .headers(headers)
            .json(request)
            .send()
            .await?;

        response.json::<OutputSchema>().await
    }
}
