# Python Telegram Bot Development Instructions

## Main Objective
Create high-quality, maintainable Python code for telegram bots using python-telegram-bot library with proper OOP design, following DRY and SOLID principles.
Code should be reusable as much as possible. Functions and methods signatures should be extendable to support multiple use cases with one function or method. 
Code must be well-structured, supportable, and must use UV for dependency management.

## Code Architecture & Design Principles

### Object-Oriented Programming Requirements
- Use proper class hierarchies and inheritance where appropriate
- Implement composition over inheritance when suitable
- Create clear interfaces and abstract base classes for extensibility
- Encapsulate data and behavior within appropriate classes
- Use dependency injection for better testability and flexibility

### DRY (Don't Repeat Yourself)
- Extract common functionality into reusable components
- Create utility classes and helper functions for repeated operations
- Use configuration classes for shared constants and settings
- Implement decorators for cross-cutting concerns (logging, error handling, rate limiting)
- If some method or function have similar functionality try to reuse it.
- Signature of function might be extended with optional params

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

### Correct handling of Telegram callbacks and commands with one method 
- Method has both update and query callback in signature
- Understands user_id
- Ensures user exists
- Uses keyboard manager to reduce memory footprint
- Uses locale manager to provide localized messages
- Replies to user using query or update
- Such method is appropriate to handle both telegram callback data and commands
```python
async def how_to(update: Update, context, query=None) -> None:
    """Send a welcome message and list available services."""
    db = context.bot_data[DB]

    user_id = update.message.from_user.id if not query else query.from_user.id
    await db.ensure_user(
        user_id,
        update.message.from_user.username if not query else query.from_user.username,
        callback=partial(on_new_user_notify, context.bot),
    )

    reply_markup = KEYBOARD_MANAGER.back_keyboard
    if not query:
        await update.message.reply_markdown(
            LOCALE_MANAGER.get("how_to_message"), reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            LOCALE_MANAGER.get("how_to_message"),
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
```

### Async/Await Implementation
- Use asyncio throughout the application
- Implement proper async context managers
- Handle async database operations correctly
- Use async/await for all I/O operations
- Implement proper error handling for async operations

### Handler Organization
- Create separate handler classes for different bot functionalities
- Use command handlers, message handlers, and callback query handlers appropriately
- Try to handle both commands and callbacks via same functions
- Implement conversation handlers for multi-step interactions
- Group related handlers into logical modules

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
- Always use UV to run pytest and python

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