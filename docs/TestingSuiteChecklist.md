# Comprehensive Testing Suite Checklist

## Summary and Goals

This testing suite aims to validate our Pathfinder 2E AI assistant backend (Frinny) by thoroughly testing both the core LangGraph agent functionality and its integration with our Foundry VTT module frontend. The primary goals of this testing effort are:

1. **Ensure Frontend-Backend Communication Integrity**: Verify that our backend correctly processes all message types from the Foundry VTT module (chat messages, combat events, character creation/level-up events) by simulating realistic frontend data patterns.

2. **Validate State Persistence**: Confirm that conversation history and context are properly maintained across multiple messages and sessions, enabling Frinny to reference previous information appropriately.

3. **Verify Response Format Consistency**: Ensure all responses include the required fields (content/message, request_id, context_id, timestamp) plus the new mood field for enhancing frontend rendering.

4. **Test System Resilience**: Validate the system's ability to handle errors, reconnections, and unexpected inputs gracefully without service disruption.

5. **Measure Performance Under Load**: Assess the backend's ability to handle multiple simultaneous users and maintain acceptable response times.

By implementing this comprehensive testing approach, we aim to deliver a robust, reliable backend service that seamlessly integrates with our Foundry VTT module while providing consistent, helpful responses to users in their Pathfinder 2E gameplay experience.

# Comprehensive Testing Suite Checklist

## 1. Testing Infrastructure Setup

- [ ] **Update Docker Compose Configuration**
   - [ ] Use SQLite for persistence
   - [ ] Update environment variables to include SQLite database path
   - [ ] Create dedicated test service for frontend simulation tests
   - [ ] Configure environment variables for testing

- [ ] **Create Test Configuration Module**
   - [ ] Define test configuration parameters (timeouts, retry counts)
   - [ ] Create test data factories for all message types
   - [ ] Setup test-specific logging configuration

## 2. Mock Frontend Data Generation

- [ ] **Create Test Data Generators**
   - [ ] Implement function to generate private chat messages
   - [ ] Implement function to generate public chat messages
   - [ ] Implement function to generate character creation data
   - [ ] Implement function to generate combat data
   - [ ] Implement function to generate level up data
   - [ ] Add randomization options for varied test scenarios

- [ ] **Validation Helpers**
   - [ ] Create schema validators for each message type
   - [ ] Implement response validators (checking for required fields)
   - [ ] Create helper for generating unique user/context IDs

## 3. Backend Integration Tests

- [ ] **Direct Agent Tests** (Bypassing WebSockets)
   - [ ] Test basic query handling and response format
   - [ ] Test conversation context persistence across multiple messages
   - [ ] Test character creation event handling
   - [ ] Test combat event handling
   - [ ] Test level up event handling
   - [ ] Test error handling and recovery

- [ ] **WebSocket API Tests**
   - [ ] Setup WebSocket client for testing
   - [ ] Test connection establishment and maintenance
   - [ ] Test sending each message type through WebSocket
   - [ ] Test WebSocket reconnection logic
   - [ ] Test concurrent WebSocket connections

## 4. Persistence Testing

- [ ] **Configure SQLite Integration**
   - [ ] Add langgraph-checkpoint-sqlite package to requirements.txt
   - [ ] Update agent.py to use SqliteSaver for state persistence
   - [ ] Configure database file path handling
   - [ ] Implement backup/recovery mechanism for the SQLite database

- [ ] **Persistence Test Cases**
   - [ ] Test short-term conversation memory (within same session)
   - [ ] Test long-term conversation memory (across sessions)
   - [ ] Test persistence with different user contexts
   - [ ] Test persistence with interleaved conversations
   - [ ] Test persistence after service restart

## 5. Response Format Testing

- [ ] **Update Response Format**
   - [ ] Add mood field to agent responses
   - [ ] Create mood analyzer function with limited set of moods (confused, happy, thinking, scared, default)
   - [ ] Implement response formatter

- [ ] **Response Validation Tests**
   - [ ] Test basic response structure (request_id, content/message, context_id)
   - [ ] Test mood field presence and valid values
   - [ ] Test timestamp field format and accuracy
   - [ ] Test error response format

## 6. Load and Performance Testing

- [ ] **Load Test Setup**
   - [ ] Create simulation for multiple concurrent users
   - [ ] Implement test for rapid message sequences
   - [ ] Configure performance metrics collection

- [ ] **Performance Test Cases**
   - [ ] Test response time under various loads
   - [ ] Test memory usage during extended sessions
   - [ ] Test SQLite performance with large conversation histories
   - [ ] Test system recovery after high load

## 7. Test Automation and CI Integration

- [ ] **Create Test Runner Scripts**
   - [ ] Implement main test runner with categorized test suites
   - [ ] Create individual test runners for specific components
   - [ ] Add command-line options for selective testing

- [ ] **CI Pipeline Integration**
   - [ ] Configure tests to run in CI environment
   - [ ] Set up test reporting and artifact collection
   - [ ] Create CI job for regression testing

## 8. Specific Implementation Tasks

- [ ] **Frontend Data Mock Implementation**
   - [ ] Create `tests/mocks/frontend_data.py` with functions for each message type
   - [ ] Implement randomization for realistic test data

- [ ] **SQLite Integration**
   - [ ] Update `app/agent/agent.py` to use SqliteSaver instead of MemorySaver
   - [ ] Configure appropriate file paths for different environments
   - [ ] Implement error handling for database access issues

- [ ] **WebSocket Testing**
   - [ ] Create `tests/test_websocket.py` with WebSocket client implementation
   - [ ] Implement message sending/receiving with proper validation

- [ ] **Response Format Update**
   - [ ] Create `app/agent/mood_analyzer.py` with mood detection logic for the required moods
   - [ ] Update `app/agent/agent.py` process_event method to include mood
   - [ ] Update response formatter to include all required fields

## 9. Documentation and Reporting

- [ ] **Test Documentation**
   - [ ] Create testing guide with examples
   - [ ] Document test data formats and expectations
   - [ ] Add inline documentation for test functions

- [ ] **Test Reporting**
   - [ ] Implement test result collection
   - [ ] Create visualization for test coverage
   - [ ] Setup automatic report generation

## 10. Error Handling and Edge Cases

- [ ] **Error Simulation Tests**
   - [ ] Test with malformed input data
   - [ ] Test with missing required fields
   - [ ] Test with extremely large messages
   - [ ] Test behavior when OpenAI API is unavailable
   - [ ] Test SQLite connection failure scenarios