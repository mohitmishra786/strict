#!/bin/bash

# Script to create P0 (CRITICAL) issues
# These are blocking issues that must be fixed first

echo "Creating P0 (CRITICAL) issues..."

# Issue 1: Fix Namespace Inconsistency
gh issue create --title "Fix Namespace Inconsistency: vaak vs rough vs strict" --label "bug" --label "enhancement" --label "help wanted" --body "**Problem:**
The codebase has namespace inconsistency:
- Source: `src/vaak/`
- Docs: `rough.integrity`
- pyproject.toml: `src/rough`
- This causes LSP errors and import issues

**Impact:**
- Blocks all development
- Import errors in IDEs
- Inconsistent package naming

**Solution:**
Standardize on `strict` (matches project name) and update:
1. All imports
2. Documentation
3. pyproject.toml
4. Test files

**Priority:** CRITICAL - Blocking all other work

**Acceptance Criteria:**
- All imports use `strict` namespace
- pyproject.toml references `src/strict`
- Documentation updated
- Tests pass with new namespace"

# Issue 2: Implement HTTP API Server
gh issue create --title "Implement HTTP API Server (Layer 1 Missing)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
No HTTP/gRPC API exists - cannot integrate with external systems

**Current State:**
- No REST endpoints
- No web interface
- Only Python library API

**Requirements:**
- FastAPI-based server
- Endpoints:
  - `POST /validate/signal` - Validate signal config
  - `POST /process/request` - Process with routing
  - `GET /health` - Health check
  - `GET /metrics` - Prometheus metrics
- Middleware: request ID, timing, CORS
- OpenAPI documentation

**Priority:** CRITICAL - Cannot use in production without API

**Acceptance Criteria:**
- FastAPI server running
- All endpoints implemented
- Health check works
- OpenAPI docs available"

# Issue 3: Add Async Support
gh issue create --title "Add Async Support for Scalability" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
All functions are synchronous (blocking) - cannot scale

**Current State:**
- All core functions are sync
- No async/await support
- Blocking I/O operations

**Requirements:**
- Add `async def` versions of all core functions
- Implement async validation with aiohttp/httpx
- Add async database/cache clients
- Update API server to use async

**Priority:** CRITICAL - Required for modern Python apps

**Acceptance Criteria:**
- All core functions have async versions
- API server uses async
- Performance benchmarks show improvement
- Tests cover async functionality"

# Issue 4: Implement Real LLM Integration
gh issue create --title "Implement Real LLM Integration (OpenAI, Ollama)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
`route_request()` returns strings but never actually calls LLMs

**Current State:**
- `route_request()` returns "cloud" or "local"
- No actual API calls to OpenAI/Anthropic/Ollama
- Core functionality missing

**Requirements:**
- Support OpenAI API
- Support Anthropic Claude
- Support local Ollama
- Support llama.cpp
- Add connection pooling
- Add request/response streaming
- Implement actual routing logic

**Priority:** CRITICAL - Core feature missing

**Acceptance Criteria:**
- Can make actual LLM calls
- Routing works between cloud/local
- Streaming support
- Error handling for failures"

# Issue 5: Add Comprehensive Observability
gh issue create --title "Add Comprehensive Observability (Logs, Metrics, Tracing)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
No logging, metrics, or tracing - blind in production

**Current State:**
- No structured logging
- No metrics collection
- No distributed tracing
- No health checks

**Requirements:**
- Structured JSON logging
- Prometheus metrics (request count, latency, errors)
- OpenTelemetry tracing
- Health check endpoints
- Error tracking (Sentry/Rollbar)

**Priority:** CRITICAL - Required for production ops

**Acceptance Criteria:**
- Structured logs available
- Prometheus metrics exposed
- Traces viewable in OpenTelemetry
- Health checks work"

echo "P0 issues created!"

echo "Next: Run P1 script for HIGH priority issues"