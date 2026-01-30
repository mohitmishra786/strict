#!/bin/bash

# Script to create P2 (MEDIUM) issues
# These are nice-to-have features

echo "Creating P2 (MEDIUM) issues..."

# Issue 10: Create CLI Tool
gh issue create --title "Create CLI Tool (Click/Typer)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
No command-line interface for developers

**Current State:**
- Only Python library API
- No CLI tools
- No interactive mode

**Requirements:**
- Click/Typer for CLI framework
- Commands:
  - `strict validate --file config.json --schema SignalConfig`
  - `strict process --input "text" --tokens 100`
  - `strict server --port 8080`
  - `strict health`
- Config file validation
- Interactive mode

**Priority:** MEDIUM - Developer experience

**Acceptance Criteria:**
- CLI commands work
- Config validation works
- Interactive mode available
- Help text comprehensive"

# Issue 11: Add Caching Layer
gh issue create --title "Add Caching Layer (Redis/Memcached)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
No caching - performance could be better

**Current State:**
- No caching layer
- Repeated validations
- No performance optimization

**Requirements:**
- Redis/Memcached integration
- LRU cache for validation results
- Cache invalidation strategies
- Cache warming
- Performance monitoring

**Priority:** MEDIUM - Performance improvement

**Acceptance Criteria:**
- Caching reduces latency
- Cache invalidation works
- Performance benchmarks show improvement
- Monitoring available"

# Issue 12: Implement Web Dashboard
gh issue create --title "Implement Web Dashboard (React/Vue)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
Text-only interface - no visual monitoring

**Current State:**
- Only CLI and API
- No web interface
- No visual metrics

**Requirements:**
- React/Vue frontend
- Real-time metrics display
- Request log viewer
- Configuration UI
- Performance charts
- Error tracking

**Priority:** MEDIUM - User experience

**Acceptance Criteria:**
- Dashboard loads
- Real-time metrics update
- Request logs viewable
- Configuration UI works"

# Issue 13: Add Plugin System
gh issue create --title "Add Plugin System (Custom Validators)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
Fixed validation logic - no extensibility

**Current State:**
- Only built-in validators
- No plugin architecture
- No custom validation rules

**Requirements:**
- Hook system for custom validators
- Plugin discovery and loading
- Hot-reload in dev mode
- Plugin registry
- Security sandboxing

**Priority:** MEDIUM - Extensibility

**Acceptance Criteria:**
- Can load custom plugins
- Plugins work correctly
- Hot-reload works
- Security sandboxing effective"

# Issue 14: Enhanced Error Handling
gh issue create --title "Enhanced Error Handling (Error Codes, Fixes)" --label "enhancement" --label "help wanted" --label "good first issue" --body "**Problem:**
Basic error messages - not helpful for debugging

**Current State:**
- Basic error messages
- No error codes
- No suggested fixes
- No error aggregation

**Requirements:**
- Error codes taxonomy
- Suggested fixes in errors
- Error aggregation and reporting
- Integration with Sentry/Rollbar
- Error classification

**Priority:** MEDIUM - Debuggability

**Acceptance Criteria:**
- Error codes consistent
- Suggested fixes provided
- Error aggregation works
- Integration with monitoring tools"

echo "P2 issues created!"

echo "Next: Run P3 script for LOW priority issues"