# **DjangoBookStore**

Online bookstore built with Django as a learning project (Hillel "Python Pro").
Users can browse the catalog, add books to a cart, place an order and pay
with Stripe. The interface is available in Ukrainian and English.

### Features

• Book catalog with categories, search by title and pagination
• CRUD for books with permission checks (add_book, change_book, delete_book)
• Custom user model (login by phone number), registration, login, logout
• Management of user permissions (can_see_user_permissions, can_set_user_permissions)
• Session cart and order creation with a confirmation email
• Stripe Checkout payment, verified on the success page and by a webhook
• Async JSON API: /books/api/books/, /books/api/books/<id>/, /books/api/stats/
• Internationalization (uk / en) with .po and .mo files in locale/
• Automated tests with pytest (unit, async and integration)

### Project structure

#### App:                          Purpose:

   books                         Book model, catalog views, async API
   categories                    Book categories
   users                         Custom user, registration, login, 
                                 permission management
   orders                        Cart, orders, Stripe payment and webhook
   tests_integration             End-to-end user flow tests
   locale                        Translations (uk, en, pl)

## Getting started

With Docker

_docker compose up --build_

The stack uses PostgreSQL and Redis. Apply migrations if needed:

_docker compose exec web python manage.py migrate_

(Replace web with the name of the Django service in docker-compose.yml.)

## Locally

_python -m venv .venv
.venv\Scripts\activate          
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver_

To run the async API through ASGI:

_python -m uvicorn DjangoBookStore.asgi:application --reload_

### Environment settings

The project expects these values in settings.py (or environment variables):
• STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET for payments
• DEFAULT_FROM_EMAIL and email backend settings for order emails
• CART_SESSION_ID — session key for the cart

## Translations

django-admin makemessages -l uk -l en
django-admin compilemessages

## Testing

pytest
The command runs all tests and prints the coverage report. The coverage
configuration is in .coveragerc and pytest.ini.
• Tools: pytest, pytest-django, pytest-asyncio, pytest-cov, factory-boy
• Stripe and email are mocked with unittest.mock
• Test data is created with factories (books/tests/factories.py,
orders/tests/factories.py, users/tests/factories.py)

## AI Usage

AI (Claude) was used in this project for three things.

    1. Code review. Three complex views were reviewed: order_success,
stripe_webhook and ManagerUserPermissionsView. The original code, the AI
recommendations, the decisions (applied or rejected) and the final code are
described in AI_REVIEW.md. Main results: payment verification
before marking an order as paid, a fixed Stripe webhook (CSRF, idempotency),
fewer SQL queries in the permissions page.

    2. Test generation. AI generated tests for the models and views. Every
generated test was run, reviewed and modified, and is marked with the comment
# Generated with AI, reviewed and modified. Several tests found real bugs
in the code (for example, Cart.clear() did not clear the cart).

    3. Documentation. Docstrings for all views and this README were written
with AI help and then checked against the code.
All prompts are listed in AI_PROMPTS.md.
What AI got wrong or needed checking: some advice had to be rejected
(for example, forbidding managers to edit their own permissions was considered
out of scope), and generated tests needed fixes (field names, order of mock
arguments, fixtures). AI output was never accepted without running the tests.

## REST API

Built with Django REST Framework. Interactive documentation (Swagger):
`/api/docs/`, ReDoc: API

Built wit OpenAPI schema:lt with Django R

| Endpoint | Description | Access |
|---|---|---|
|ctive documenta| Books (filters, search, ordering) | read: everyone, write: admin |
|on (Swagger):
`/api/| Categories with books count | read: everyone, write: admin |
|entation (Swagge| Orders with nested items,ngo REST Framework. In| authenticated, owner only |
|REST Framework| Session cart:ilt wit## REST AP## REST A| everyone |
|uilt with Django REST F| Registration | everyone |
|o REST Framewor## REST API

Built with## REST API

Built wit| JWT | everyone |
|ith Django REST Fr| Current user | authenticated |

- Pagination: 20 items per page (`?page=2`)
- Filters:i/docs/`, ReDoc: `/api/redoc/`, OpenAPI schema: `/api/schema## REST API
## REST API

Built w- Throttling: 100 requests/hour for anonymous, 1000/hour for authenticated users
- Authorization: ReDoc: `/api/redoc/`, OpenAPI schema: `- CORS: allowed origins are set inT Framework. Interactive- Permissions:uilt with Django REST## REST API

Built wi(see `api/permissions.py`)