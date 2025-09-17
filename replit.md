# Overview

This is a FastAPI-based MCP (Model Context Protocol) server that provides a wrapper around the UiTdatabank Search API. UiTdatabank is a Belgian cultural events database that provides information about events, places, and organizers. The application serves as a bridge between MCP clients and the UiTdatabank API, allowing users to search for cultural events and venues in Belgium through a standardized interface.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework
- **FastAPI**: Chosen as the web framework for its automatic API documentation, type hints support, and high performance
- **FastMCP**: Used to implement the Model Context Protocol server functionality, enabling integration with MCP-compatible clients
- **Uvicorn**: ASGI server for running the FastAPI application with support for async operations

## API Integration Pattern
- **HTTP Client**: Uses `httpx` for making asynchronous HTTP requests to the UiTdatabank API
- **Authentication Strategy**: Implements client ID-based authentication using both header (`x-client-id`) and query parameter (`clientId`) approaches for maximum compatibility
- **Search Abstraction**: Provides a unified search interface across different UiTdatabank endpoints (events, places, organizers)

## Configuration Management
- **Environment Variables**: Uses `python-dotenv` for loading configuration from environment variables
- **Secret Management**: API credentials are managed through environment variables for security

## Error Handling and Reliability
- **Graceful Degradation**: The authentication system works with or without client credentials
- **Type Safety**: Extensive use of Python type hints for better code reliability and IDE support

# External Dependencies

## Primary API Integration
- **UiTdatabank Search API**: Belgian cultural database API at `https://search.uitdatabank.be`
  - Provides access to events, places, and organizers data
  - Requires client ID for authentication
  - Supports various search parameters including location, date ranges, and text queries

## Python Dependencies
- **fastapi**: Web framework for building the API server
- **uvicorn[standard]**: ASGI server with standard extras for production deployment
- **httpx**: Modern async HTTP client for external API calls
- **fastmcp**: Model Context Protocol implementation for Python
- **python-dotenv**: Environment variable management for configuration

## Runtime Environment
- **Python 3.7+**: Required for FastAPI and async/await support
- **Port 5000**: Default application port, configurable through the uvicorn runner
- **Host 0.0.0.0**: Configured for containerized or network deployment scenarios