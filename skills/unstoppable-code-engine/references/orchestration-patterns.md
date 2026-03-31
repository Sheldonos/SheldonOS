# Orchestration Patterns for Sub-Agent Management

This document provides guidance on when and how to spawn sub-agents to maximize development efficiency while maintaining quality and integration.

## When to Spawn Sub-Agents

Spawn sub-agents when the project meets one or more of these criteria:

### 1. Multi-Component Architecture
The project has distinct, separable components that can be developed independently:
- Frontend + Backend + Database
- Multiple microservices
- Plugin system with independent modules
- Multi-platform applications (web + mobile)

### 2. Parallel Independent Tasks
Multiple tasks can be executed simultaneously without dependencies:
- Integrating multiple third-party APIs
- Building multiple independent features
- Creating test suites for different modules
- Generating documentation and code simultaneously

### 3. Specialized Domain Expertise
The project requires deep focus in specialized areas:
- Machine learning model + web interface
- Complex data processing + visualization dashboard
- Security implementation + application logic
- Performance optimization + feature development

### 4. Scale and Complexity
The project is large enough that division of labor provides clear benefits:
- More than 1000 lines of code expected
- Multiple distinct user flows
- Complex state management
- Extensive testing requirements

## Sub-Agent Spawning Strategies

### Strategy 1: Component-Based Division

Divide the project by architectural components.

**Example**: Building a full-stack web application
- **Sub-Agent A**: Frontend (React, UI/UX, client-side logic)
- **Sub-Agent B**: Backend (API, business logic, authentication)
- **Sub-Agent C**: Database (schema design, migrations, queries)

**Your Role**: System architect and integrator. Define clear interfaces between components and validate integration.

### Strategy 2: Feature-Based Division

Divide the project by independent features or user stories.

**Example**: Building a project management tool
- **Sub-Agent A**: User authentication and profile management
- **Sub-Agent B**: Task creation and assignment system
- **Sub-Agent C**: Notification and messaging system

**Your Role**: Product manager and integration lead. Ensure features work together cohesively.

### Strategy 3: Layer-Based Division

Divide the project by technical layers or concerns.

**Example**: Building a data analytics platform
- **Sub-Agent A**: Data ingestion and ETL pipeline
- **Sub-Agent B**: Analysis engine and algorithms
- **Sub-Agent C**: Visualization and reporting interface

**Your Role**: Technical lead. Ensure data flows correctly through all layers.

### Strategy 4: Parallel Specialization

Assign sub-agents to work on different specialized aspects simultaneously.

**Example**: Building a production-ready application
- **Sub-Agent A**: Core feature implementation
- **Sub-Agent B**: Comprehensive test suite
- **Sub-Agent C**: Documentation and deployment scripts

**Your Role**: Quality assurance lead. Validate that all aspects meet production standards.

## Effective Sub-Agent Management

### 1. Clear Objective Definition

When spawning a sub-agent, provide:
- **Specific Goal**: What exactly needs to be built
- **Success Criteria**: How to know when it's done
- **Interface Requirements**: How it integrates with other components
- **Technical Constraints**: Languages, frameworks, patterns to follow

**Example**:
```
Build a REST API for user authentication with the following requirements:
- Endpoints: POST /register, POST /login, POST /logout, GET /profile
- JWT-based authentication
- Password hashing with bcrypt
- Input validation for all endpoints
- Success criteria: All endpoints return correct status codes and data structures
- Must integrate with PostgreSQL database schema (provided)
```

### 2. Right-Sizing Tasks

Ensure each sub-agent receives an appropriately sized task:
- **Too Small**: Overhead of spawning exceeds benefit
- **Too Large**: Sub-agent becomes overwhelmed or loses focus
- **Just Right**: Sub-agent can complete task independently with clear deliverables

**Rule of Thumb**: Each sub-agent should produce 200-1000 lines of code or equivalent work.

### 3. Monitoring and Validation

After spawning sub-agents:
1. **Track Progress**: Monitor each sub-agent's output
2. **Validate Deliverables**: Test each component independently before integration
3. **Request Revisions**: If output doesn't meet standards, provide specific feedback
4. **Integrate Incrementally**: Combine components one at a time, testing after each integration

### 4. Integration Responsibility

You are responsible for:
- Defining clear interfaces between components
- Resolving conflicts or inconsistencies
- Ensuring components work together seamlessly
- Final end-to-end testing of the integrated system

## Anti-Patterns to Avoid

### ❌ Over-Fragmentation
Spawning too many sub-agents for trivial tasks creates coordination overhead.

**Bad**: Spawning 10 sub-agents to each write a single function
**Good**: Spawning 3 sub-agents to each build a complete module

### ❌ Unclear Boundaries
Sub-agents with overlapping responsibilities create conflicts and duplication.

**Bad**: Two sub-agents both implementing user authentication
**Good**: One sub-agent for authentication, another for authorization

### ❌ Weak Integration Planning
Spawning sub-agents without defining how components will integrate.

**Bad**: "Build a frontend" and "Build a backend" with no API specification
**Good**: Define API contract first, then spawn frontend and backend sub-agents

### ❌ Abdication of Responsibility
Spawning sub-agents and assuming they will handle everything.

**Bad**: Spawning sub-agents and not validating their output
**Good**: Spawning sub-agents, validating deliverables, and ensuring integration

## Integration Checklist

Before declaring a multi-agent project complete:

- [ ] All sub-agent deliverables received and validated independently
- [ ] Interface contracts between components are respected
- [ ] Components integrated and tested together
- [ ] End-to-end user flows tested successfully
- [ ] Error handling works across component boundaries
- [ ] Performance is acceptable under realistic conditions
- [ ] Code quality is consistent across all components
- [ ] Documentation covers the integrated system

## Example: Full-Stack Application

**Project**: Build a task management web application

**Decomposition**:
1. **Sub-Agent: Frontend Developer**
   - Build React application with task list, task creation, and task editing
   - Implement responsive design
   - Connect to backend API
   - Success: All UI components render correctly and interact with API

2. **Sub-Agent: Backend Developer**
   - Build Express.js API with CRUD endpoints for tasks
   - Implement authentication middleware
   - Connect to database
   - Success: All API endpoints return correct data and status codes

3. **Sub-Agent: Database Engineer**
   - Design PostgreSQL schema for users and tasks
   - Write migration scripts
   - Create seed data for testing
   - Success: Schema supports all required queries efficiently

**Your Integration Work**:
1. Define API contract (endpoints, request/response formats)
2. Spawn all three sub-agents with clear specifications
3. Validate each component independently
4. Integrate frontend with backend
5. Test end-to-end user flows
6. Deploy and validate in production-like environment

**Result**: A fully functional, production-ready task management application.
