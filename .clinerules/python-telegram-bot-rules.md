# Python Telegram Bot Development Instructions

## Main Objective
Create high-quality, maintainable Telegram bots using python-telegram-bot library with proper OOP design, following DRY and SOLID principles. Code must be well-structured, supportable, and use UV for dependency management.

## Code Architecture & Design Principles

### Object-Oriented Programming Requirements
- Use proper class hierarchies and inheritance where appropriate
- Implement composition over inheritance when suitable
- Create clear interfaces and abstract base classes for extensibility
- Encapsulate data and behavior within appropriate classes
- Use dependency injection for better testability and flexibility

### SOLID Principles Implementation
- **Single Responsibility**: Each class should have one reason to change
- **Open/Closed**: Classes should be open for extension, closed for modification
- **Liskov Substitution**: Derived classes must be substitutable for their base classes
- **Interface Segregation**: Create specific interfaces rather than general-purpose ones
- **Dependency Inversion**: Depend on abstractions, not concretions

### DRY (Don't Repeat Yourself)
- Extract common functionality into reusable components
- Create utility classes and helper functions for repeated operations
- Use configuration classes for shared constants and settings
- Implement decorators for cross-cutting concerns (logging, error handling, rate limiting)

## File Structure & Size Constraints

### File Size Limitations
- Maximum 350 lines of code per Python file
- Maximum 6000 words per file
- When files exceed these limits, refactor into smaller, focused modules
- Consider splitting large classes into multiple files using composition

### Recommended Project Structure
```
project_root/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── handlers/
│   │   ├── services/
│   │   ├── models/
│   │   └── utils/
│   ├── config/
│   └── database/
├── pyproject.toml
└── uv.lock
```

## Python-Telegram-Bot Specific Requirements

### Async/Await Implementation
- Use asyncio throughout the application
- Implement proper async context managers
- Handle async database operations correctly
- Use async/await for all I/O operations
- Implement proper error handling for async operations

### Handler Organization
- Create separate handler classes for different bot functionalities
- Use command handlers, message handlers, and callback query handlers appropriately
- Implement conversation handlers for multi-step interactions
- Group related handlers into logical modules

### Bot Architecture Patterns
- Use Application class from python-telegram-bot v20+
- Implement proper bot initialization and shutdown procedures
- Use context objects effectively for state management
- Create service layer for business logic separation from handlers

## Code Quality Standards

### Error Handling
- Implement comprehensive exception handling
- Create custom exception classes for domain-specific errors
- Use proper logging for error tracking and debugging
- Implement graceful degradation for non-critical failures

### Configuration Management
- Use environment variables for sensitive data
- Create configuration classes with validation
- Support multiple environments (development, staging, production)
- Implement configuration inheritance for shared settings

### Database Integration
- Use async database drivers (asyncpg, motor, etc.)
- Implement repository pattern for data access
- Use connection pooling for better performance
- Create proper database migrations and schema management

## Dependency Management

### UV Requirements
- Always use UV as the dependency management tool
- Create proper pyproject.toml with all dependencies
- Pin dependency versions for production stability
- Use dependency groups for development, testing, and optional features
- Keep uv.lock file in version control

### Virtual Environment
- Use UV to create and manage virtual environments
- Document environment setup procedures
- Ensure reproducible builds across different systems

## Code Style & Formatting

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints throughout the codebase
- Implement proper docstrings for classes and methods
- Use meaningful variable and function names
- Keep functions focused and small (max 20-30 lines)

### Import Organization
- Group imports: standard library, third-party, local imports
- Use absolute imports over relative imports
- Sort imports alphabetically within groups
- Remove unused imports

## Documentation & Testing Policy

### Limited Documentation Scope
- Create documentation files **only when explicitly requested by user**
- Focus on inline code comments and docstrings for self-documenting code
- Include README.md only if specifically asked

### Testing Policy
- Write tests **only when explicitly specified by user**
- Focus on unit tests for business logic
- Create integration tests for bot handlers when requested
- Use pytest with async support for testing

### Demo Scripts
- Create showcase or demo scripts **only upon explicit user request**
- Keep demo scripts simple and focused on specific features
- Include proper setup instructions when demos are created

## Performance & Scalability

### Async Best Practices
- Use connection pooling for database operations
- Implement proper rate limiting for API calls
- Use caching strategies for frequently accessed data
- Optimize database queries and avoid N+1 problems

### Resource Management
- Implement proper connection cleanup
- Use context managers for resource handling
- Monitor memory usage in long-running operations
- Implement graceful shutdown procedures

## Main Objective
Develop maintainable, well-architected Python Telegram bots using python-telegram-bot library with strict adherence to OOP principles, DRY and SOLID design patterns, file size constraints, and UV dependency management. Create clean, supportable code that follows industry best practices while focusing on core functionality over extensive documentation unless explicitly requested.