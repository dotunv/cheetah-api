# Cheetah Platform Backend Development Tasks

This document outlines the key tasks for building the FastAPI backend for the Cheetah InterCity transportation aggregator platform. Tasks are grouped by module/feature and prioritized for MVP.

## Phase 0: Setup & Foundation (MVP Prerequisite)

### Project Initialization
- [x] Create project directory `cheetah-api/`
- [x] Initialize Git repository
- [x] Create Python virtual environment
- [x] Install core dependencies: `fastapi`, `uvicorn`, `sqlmodel`, `psycopg2-binary`, `python-dotenv`, `passlib[bcrypt]`, `python-jose[cryptography]`, `httpx`
- [x] Set up `.gitignore` (include `.env`, `__pycache__`, virtual environment folder)
- [x] Configure `pyproject.toml` (or `requirements.txt`) for dependency management

### Core Application Structure
- [x] Create `app/` directory as the main Python package
- [x] Create `app/__init__.py` (empty file)
- [x] Create `app/main.py` (FastAPI app entry point)
- [x] Create `app/database/` directory
  - [x] `app/database/__init__.py`
  - [x] `app/database/config.py` (for loading environment variables)
  - [x] `app/database/database.py` (engine, session management, lifespan event)
  - [x] `app/database/models.py` (initial SQLModel definitions: User, Booking)
- [x] Create `app/routers/` directory
  - [x] `app/routers/__init__.py`
  - [x] `app/routers/users.py` (initial user endpoints)
  - [x] `app/routers/auth.py` (authentication endpoints)
- [x] Create `app/services/` directory
  - [x] `app/services/__init__.py`
  - [x] `app/services/user_service.py` (user-related business logic)
  - [x] `app/services/auth_service.py` (authentication logic, password hashing, JWT handling)
- [x] Create `.env` file with `DATABASE_URL` and `SECRET_KEY` for JWT

### Basic Security Implementation
- [x] Implement password hashing (using `passlib[bcrypt]`) for user registration
- [x] Implement JWT-based authentication (`python-jose`) for user login and token generation
- [x] Secure basic routes using FastAPI's `Depends` for authentication

### Database Setup & Migrations (Alembic)
- [ ] Initialize Alembic within the project
- [ ] Configure `alembic.ini` to point to your `SQLModel.metadata`
- [ ] Generate initial migration for User and Booking models
- [ ] Apply initial migration to the database
- [ ] Document Alembic migration workflow

## Phase 1: MVP Core Features

### 1. Unified Search & Booking

#### Database Models
- [x] Define `TransportProvider` model (name, type, contact, API key/credentials)
- [x] Define `Route` model (origin, destination, common route ID, associated providers)
- [x] Define `Schedule` model (provider_id, route_id, departure_time, arrival_time, duration, available_seats, base_price)
- [x] Refine `Booking` model (add fields for selected schedule, passenger details, payment status)

#### Transport Provider Integration Module (`app/services/transport_provider_service.py`)
- [x] **Mock API Integration**: Create a mock client that simulates responses from 2-3 transport providers
  - [x] Mock `get_schedules(origin, destination, date)`
  - [x] Mock `get_pricing(schedule_id, seats)`
  - [x] Mock `book_ticket(schedule_id, passenger_details)`
- [x] Implement a data normalization layer to standardize responses from different providers

#### Booking Service (`app/services/booking_service.py`)
- [x] Implement `search_routes(origin, destination, date, filters)`:
  - [x] Call `transport_provider_service` for all enabled providers concurrently (using `asyncio.gather`)
  - [x] Aggregate and normalize results
  - [x] Sort and filter options based on user criteria (price, duration, type)
- [x] Implement `create_booking(user_id, selected_option, passenger_details)`:
  - [x] Call the specific transport provider's booking API (mock initially)
  - [x] Save booking details to the database
  - [x] Trigger insurance auto-enrolment (background task)
  - [x] Trigger Wi-Fi code generation (background task)
  - [x] Update Schedule model (reduce available_seats)

#### User-Facing Endpoints (`app/routers/bookings.py`)
- [x] `GET /search/` (unified search, requires authentication if desired, but guest checkout is allowed)
- [x] `POST /bookings/` (create a booking, requires authentication or guest email)
- [x] `GET /users/{user_id}/bookings/` (retrieve user's booking history)
- [x] `GET /bookings/{booking_id}/` (retrieve single booking details)

### 2. Free Accident Insurance

#### Database Model
- [x] Define `InsurancePolicy` model (booking_id, policy_number, coverage_details_url, status, start_date, end_date)

#### Insurance Integration Module (`app/services/insurance_service.py`)
- [x] **Mock API Integration**: Create a mock client for the insurance partner
  - [x] Mock `enroll_policy(passenger_details, booking_details)`: returns a mock policy number and URL
- [x] Implement `auto_enroll_for_booking(booking_id, passenger_details)`:
  - [x] Calls mock insurance API
  - [x] Stores `InsurancePolicy` in the database

#### Integration with Booking Flow
- [x] Modify `booking_service.create_booking` to call `insurance_service.auto_enroll_for_booking` as a `BackgroundTasks` task

#### User-Facing Endpoints (`app/routers/insurance.py`)
- [ ] `GET /users/{user_id}/insurance_policies/` (list policies for a user)
- [ ] `GET /insurance_policies/{policy_id}/` (retrieve single policy details)

### 3. Free Wi-Fi Access

#### Database Model
- [x] Define `WifiCode` model (booking_id, code, expiry_time, usage_status)

#### Wi-Fi Management Module (`app/services/wifi_service.py`)
- [x] **Mock API Integration**: Create a mock client for Wi-Fi providers
  - [x] Mock `generate_code(duration_minutes)`: returns a static/dummy Wi-Fi code
- [x] Implement `generate_wifi_code_for_booking(booking_id)`:
  - [x] Calls mock Wi-Fi API
  - [x] Stores `WifiCode` in the database

#### Integration with Booking Flow
- [x] Modify `booking_service.create_booking` to call `wifi_service.generate_wifi_code_for_booking` as a `BackgroundTasks` task

#### User-Facing Endpoints (`app/routers/wifi.py`)
- [ ] `GET /users/{user_id}/wifi_codes/` (list Wi-Fi codes for upcoming/active bookings)
- [ ] `GET /wifi_codes/{code_id}/qr_code` (endpoint to generate QR code image/data - consider client-side generation for simplicity in MVP)

### 4. User Accounts & Notifications

#### Refine User Account Endpoints (`app/routers/users.py`, `app/routers/auth.py`)
- [x] `POST /users/register` (already started)
- [x] `POST /auth/token` (login, JWT generation - already started)
- [x] `GET /users/me` (get current user profile)
- [x] `PUT /users/me` (update user profile)
- [x] **Guest checkout implementation**: Ensure booking endpoint can accept email instead of user_id for guest bookings

#### Notification System (`app/services/notification_service.py`)
- [x] Implement `send_email(recipient, subject, body)` utility
- [x] Implement `send_sms(recipient, message)` utility
- [x] **Booking Confirmation**: Trigger `notification_service.send_email` and `send_sms` (as `BackgroundTasks`) post-booking with:
  - [x] Booking details
  - [x] Insurance certificate details/link
  - [x] Wi-Fi access codes
- [x] Basic error handling for notification failures

## Phase 2: Backend/Admin Features (Post-MVP)

### Transport Provider Management Module (`app/routers/providers.py`, `app/services/provider_management_service.py`)
- [ ] Authentication/Authorization for providers to access their specific endpoints
- [ ] `POST /providers/{provider_id}/schedules/batch` (for batch uploads)
- [ ] `PUT /providers/{provider_id}/schedules/{schedule_id}` (update specific schedule)
- [ ] `POST /providers/{provider_id}/webhooks/schedule_update` (endpoint for providers to push real-time updates)
- [ ] Implement data validation for provider uploads

### Insurance Module Refinement
- [ ] Implement claims reporting interface (API endpoints and logic)
- [ ] Integrate with actual insurance partner API (replace mock)
- [ ] Handle policy cancellations/refunds in coordination with booking cancellations

### Wi-Fi Management Refinement
- [ ] Integrate with actual Wi-Fi provider API (replace mock)
- [ ] Implement usage monitoring and bandwidth allocation APIs
- [ ] Implement troubleshooting tools for Wi-Fi access issues

### Analytics Dashboard (`app/routers/analytics.py`, `app/services/analytics_service.py`)
- [ ] `GET /admin/analytics/booking_trends` (filters by date, provider, route)
- [ ] `GET /admin/analytics/user_demographics`
- [ ] `GET /admin/analytics/provider_performance`
- [ ] Data aggregation and reporting logic
- [ ] Secure these endpoints with admin-level authorization

## Phase 3: Advanced Features & Refinements (Beyond MVP)

### Payment Gateway Integration
- [ ] Integrate with a secure payment gateway (e.g., Paystack, Stripe, Flutterwave - depending on region)
- [ ] Handle payment processing, success, and failure callbacks
- [ ] Implement refund and cancellation logic
- [ ] Ensure PCI-DSS compliance (largely handled by the gateway, but your integration must be secure)

### Real-time Data Sync (Non-mock)
- [ ] Implement robust error handling, retries, and circuit breakers for external API calls
- [ ] Implement caching (e.g., Redis) for frequently accessed, less volatile data (e.g., static route information)
- [ ] Explore WebSockets for real-time seat availability updates (if frontend requires it)

### Reviews & Ratings
- [ ] Database models for `Review` (user_id, provider_id, rating, comment)
- [ ] Endpoints for submitting and retrieving reviews

### Customer Support Integrations
- [ ] Integrate with a live chat/ticketing system API
- [ ] (Future) Implement a basic chatbot integration for FAQs

### Discounts & Loyalty
- [ ] Database models for `PromoCode`, `LoyaltyPoint`
- [ ] Endpoints for applying promo codes during booking
- [ ] Logic for accumulating and redeeming loyalty points

### Scalability & Observability
- [ ] Implement comprehensive logging (e.g., `structlog`)
- [ ] Set up monitoring and alerting (e.g., Prometheus, Grafana, AWS CloudWatch)
- [ ] Distributed Tracing (e.g., OpenTelemetry) for complex microservice interactions
- [ ] Optimize database queries and indexing

### Deployment Automation (CI/CD)
- [ ] Set up Dockerfiles for your FastAPI application
- [ ] Implement CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins, etc.) for automated testing and deployment to AWS/GCP
- [ ] Container orchestration with Kubernetes (EKS/GKE) for high availability and scalability

## Ongoing Tasks

### Testing
- [ ] Write unit tests for all services and utility functions
- [ ] Write integration tests for API endpoints
- [ ] Set up a testing pipeline (e.g., Pytest)

### Documentation
- [ ] Maintain comprehensive API documentation (FastAPI's auto-generated docs are a great start)
- [ ] Document internal architecture, design decisions, and common workflows

### Security Audits
- [ ] Regularly review code for security vulnerabilities
- [ ] Stay updated on FastAPI security best practices

### Compliance
- [ ] Ensure ongoing GDPR/CCPA adherence for data privacy
- [ ] Regularly review insurance and Wi-Fi disclaimers and legal terms







