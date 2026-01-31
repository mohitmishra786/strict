import axios from 'axios';

export enum SignalType {
  ANALOG = 'analog',
  DIGITAL = 'digital',
  HYBRID = 'hybrid',
}

export enum ProcessorType {
  CLOUD = 'cloud',
  LOCAL = 'local',
  HYBRID = 'hybrid',
}

export interface ProcessingRequest {
  input_data: string;
  input_tokens: number;
  processor_type?: ProcessorType;
  timeout_seconds?: number;
}

export interface ValidationResult {
  status: string;
  is_valid: boolean;
  input_hash: string;
  errors: string[];
}

export interface OutputSchema {
  result: any;
  validation: ValidationResult;
  processor_used: ProcessorType;
  processing_time_ms: number;
}

export class StrictClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async processRequest(request: ProcessingRequest): Promise<OutputSchema> {
    const response = await axios.post(`${this.baseUrl}/process/request`, request, {
      headers: this.apiKey ? { 'X-API-Key': this.apiKey } : {},
    });
    return response.data;
  }

  async healthCheck(): Promise<any> {
    const response = await axios.get(`${this.baseUrl}/health`);
    return response.data;
  }
}
