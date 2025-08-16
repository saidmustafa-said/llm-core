<!-- @format -->

# LLM Engine – Intelligent Location Discovery System

A robust conversational AI platform designed for real-world, scalable agentic workflows. The system excels at location-based advice and recommendations, leveraging modular agents, persistent state, and advanced error handling to deliver reliable, context-aware responses.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Configuration](#configuration)
- [System Flow](#system-flow)
- [Development Principles](#development-principles)
- [Vision & Future Directions](#vision--future-directions)

---

## Overview

LLM Engine is built to bridge the gap between demo-perfect AI and the unpredictable "last mile" of real user workflows. The system is designed to handle large, complex environments (e.g., thousands of database tables or POIs) by dividing tasks among specialized agents and merging results, ensuring scalability and adaptability.

---

## Architecture

### 🎯 Architectural Approach

The LLM Engine is designed to excel in real-world environments where complexity, scale, and unpredictability are the norm. The architecture reflects a philosophy of building systems that adapt to user context, handle edge cases gracefully, and remain robust under demanding conditions.

- **Scalable Agentic Workflows:** The system divides complex tasks into specialized agents, each responsible for a distinct function. This modularity allows the engine to handle large datasets, diverse user requests, and evolving business logic without bottlenecks.

- **Contextual State & Memory Management:** Persistent state and history managers ensure that every agent has access to relevant context, enabling multi-turn reasoning and continuity across sessions. This approach supports workflows where the outcome of one agent influences the next, allowing for adaptive, stateful interactions.

- **Configurable & Extensible:** All agent behaviors, provider integrations, and system parameters are managed through configuration. This makes it easy to tailor the engine to new domains, scale up to more agents, or optimize for specific business needs.

- **Resilient Error Handling & Observability:** The architecture includes dedicated error agents and a unified status code system, transforming technical failures into actionable, user-friendly feedback. File-based, session-grouped logging provides deep insight into agent decisions and system health, supporting rapid debugging and continuous improvement.

- **Advanced Prompt Engineering:** Prompts are crafted to guide agents toward reliable, goal-oriented behavior. The system leverages positive reinforcement and systemic prompt layouts, ensuring agents remain focused and minimize off-task responses—even in complex, multi-step reasoning scenarios.

- **Vision for Agent Generation:** The platform is built to support the rapid creation and deployment of thousands of specialized agents, each with clear input/output formats and the ability to communicate and collaborate. This paves the way for automating manual workflows and scaling AI solutions to enterprise levels.

---

### 🏗️ Infrastructure Layer

- **Cache:** Specialized cache types for performance.
- **Status Codes:** Unified error/component tracking (XYZAB format).
- **Logging:** File-based, session-grouped logs for observability and debugging.
- **Configuration:** Centralized management for all services.
- **State & History:** Persistent session and conversation tracking.
- **Data Access:** Unified layer for POI and geospatial queries.
- **LLM Endpoints:** Multi-provider integration with adaptive model selection.

---

### 🤖 Agent System

- **Main Orchestrator:** Manages conversations, agent invocation, and session context.
- **Location Agent:** Handles location search, classification, and POI management.
- **Advice Agent:** Generates personalized recommendations.
- **Error Handler:** Provides context-aware, solution-oriented error responses.

---

## Key Features

- **Divide-and-Conquer Agentic Workflows:** Scales to large datasets and complex environments by splitting tasks and merging results.
- **Session & History Management:** Tracks user actions and context for coherent multi-turn interactions.
- **Configurable Agents:** Easily adapt agent behaviors and providers for different business needs.
- **Observability:** Unified logging and status codes for deep insight into agent decisions and system health.
- **Prompt Engineering:** Systemic, context-driven prompts with positive reinforcement for reliable agent behavior.

---

# LLM Engine – Project README

## Overview

LLM Engine is a modular conversational AI system designed for intelligent location-based recommendations and advice. It combines agentic workflows, persistent state, and robust error handling to deliver reliable, context-aware responses for real-world applications.

---

## Features

- Modular agent architecture for location discovery, advice, and error handling
- Persistent state and history management for multi-turn conversations
- Centralized configuration for easy customization and extensibility
- Unified logging and status code system for observability and debugging
- Scalable design for large datasets and complex user workflows

---

## Architecture

### System Components

- **API Layer:** Entry point for user queries and integration with external systems (`api.py`)
- **Main Orchestrator:** Coordinates agent execution, manages session state, and integrates responses
- **Agents:** Specialized modules for location search, advice generation, and error handling
- **State Manager:** Tracks session state, user context, and agent actions
- **History Manager:** Records all interactions for context-aware reasoning and continuity
- **Cache Manager:** Optimizes performance for repeated queries and data access
- **Configuration System:** Centralizes all settings, agent behaviors, and provider integrations (`config.json`)
- **Logging System:** Captures agent decisions, errors, and system health for monitoring and debugging

### Data Flow

1. **User Request:** API receives a query with location and intent
2. **Session Context:** Orchestrator loads session state and history
3. **Agent Execution:** Location, advice, and error agents process the request
4. **Response Integration:** Orchestrator merges agent outputs into a natural language response
5. **State & History Update:** Session state and history are updated for future interactions
6. **Logging & Status Codes:** All actions and errors are logged with standardized codes

---

## State, History, and Configuration

- **State Management:** Each user session is tracked with a dedicated state manager, allowing agents to adapt responses based on previous actions and current context. State is persisted using a JSON backend for reliability and transparency.

- **History Management:** All user interactions and agent responses are recorded, enabling agents to reference past conversations and maintain continuity. History is managed via a JSON backend and stored in the configured directory.

- **Configuration:** The system is fully configurable via `config.json`, including environment settings, backend choices, data paths, and agent/provider parameters. This allows rapid adaptation to new domains and requirements without code changes.

---

## Setup & Installation

1. **Python 3.10+ required**
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   On Windows:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the API server:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## Usage Example

Send a POST request to `/query`:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "i want to go to somewhere with a great view where i can also drink something", "latitude": 40.985660, "longitude": 29.027361, "radius": 5000, "num_results": 5}'
```

---

## Project Structure

```
llm-engine/
├── api.py                  # API entry point
├── main.py                 # Main application logic
├── config.json             # System configuration
├── requirements.txt        # Python dependencies
├── src/
│   ├── core/               # Core data types and flow management
│   ├── llm/                # LLM integration and interface
│   ├── location_poi/       # Location and POI logic
│   ├── managers/           # State, history, cache, flow managers
│   ├── utils/              # Utility functions
│   └── ...                 # Additional modules
└── ...
```

---

## Development Principles

- Clean, readable code with clear separation of concerns
- Minimal, standalone components for each system function
- Configuration-driven logic for flexibility and maintainability
- Persistent state and history for robust multi-turn reasoning
- Unified logging and error handling for observability

---

## Documentation & References

- See `docs/` for architecture, status codes, and development phases
- For advanced concepts, review the Future Concept Protocol documentation

---

**LLM Engine is built for reliability, extensibility, and clarity—ready for real-world deployment and intelligent location-based recommendations.**
