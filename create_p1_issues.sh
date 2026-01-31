#!/bin/bash
set -euo pipefail

# Script to create P1 (HIGH) issues
# These are important but not blocking

# Check if gh CLI is available and authenticated
if ! gh auth status &>/dev/null; then
    echo "Error: gh CLI not authenticated. Run 'gh auth login' first."
    exit 1
fi

echo "Creating P1 (HIGH) issues..."

# Issue 6: Add Persistence Layer
gh issue create --title "Add Persistence Layer (PostgreSQL, Redis, S3)" --label "enhancement" --label "help wanted" --body "**Problem:**
No storage beyond memory - data not persisted

**Current State:**
- All data in memory
- No database persistence
- No caching layer
- No object storage

**Requirements:**
- PostgreSQL adapter for structured data
- Redis for caching
- S3 for large objects
- In-memory for dev/testing
- SQLAlchemy models
- Connection pooling

**Priority:** HIGH - Data durability required

**Acceptance Criteria:**
- Can store and retrieve data
- Caching improves performance
- Large objects stored in S3
- Connection pooling works"

# Issue 7: Add Authentication & Authorization
gh issue create --title "Add Authentication & Authorization (JWT, API Keys)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
No security - anyone can access API

**Current State:**
- No authentication
- No authorization
- No API keys
- No RBAC

**Requirements:**
- JWT token authentication
- API key support
- RBAC (Role-Based Access Control)
- OAuth2 integration
- Rate limiting integration

**Priority:** HIGH - Security required

**Acceptance Criteria:**
- JWT authentication works
- API keys can be generated
- Role-based access control
- Rate limiting enforced"

# Issue 8: Add Real Signal Processing
gh issue create --title "Add Real Signal Processing (scipy.signal)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
Only Nyquist math - no actual signal processing

**Current State:**
- Only Nyquist criterion validation
- No FFT, filtering, windowing
- No spectral analysis
- No wavelet transforms

**Requirements:**
- Integrate with scipy.signal
- FFT, filtering, windowing
- Spectral analysis
- Wavelet transforms
- Signal visualization

**Priority:** HIGH - Differentiator feature

**Acceptance Criteria:**
- Can perform FFT on signals
- Can filter signals
- Can analyze frequency content
- Signal visualization works"

# Issue 9: Expand Validation Coverage
gh issue create --title "Expand Validation Coverage (CSV, XML, Binary)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
Limited validation - only 5 main models

**Current State:**
- Only SignalConfig, ProcessingRequest, etc.
- No CSV/TSV validation
- No XML validation
- No binary data validation
- No streaming validation

**Requirements:**
- Add CSV/TSV validation
- Add XML validation
- Add binary data validation
- Add streaming validation (chunked)
- Add nested object validation with paths
- Add custom validator plugins

**Priority:** HIGH - Flexibility needed

**Acceptance Criteria:**
- Can validate CSV files
- Can validate XML
- Can validate binary data
- Can validate streaming data"

echo "P1 issues created!"

echo "Next: Run P2 script for MEDIUM priority issues"