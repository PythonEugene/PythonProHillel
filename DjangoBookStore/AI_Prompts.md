# **AI Prompts**

List of prompts used while working on the "AI for improving the project"
assignment. AI: Claude.

## 1. Code review

_Prompt 1 — order_success_

Do a code review of this Django view. Look for security problems, bugs and
bad practices.
(code of order_success attached)
Result: found that an order is marked PAID without payment verification.
Applied: check the payment with Stripe before changing the status.

_Prompt 2 — stripe_webhook_

Review this Stripe webhook view for Django. What can break in production?
(code of stripe_webhook attached)
Result: missing @csrf_exempt and @require_POST, outdated
stripe.error, no protection against repeated events. Applied all.

_Prompt 3 — ManagerUserPermissionsView_

Review this Django class-based view and its form. Look for performance
problems, security and readability.
(code of the view and UserPermissionForm attached)
Result: repeated queries for the same user, N+1 in the form, implicit
permission check. Applied all except forbidding a manager to edit their own
permissions.

_Prompt 4 — fixing the tests after the review_

After the fix of order_success my test fails. How should I mock the
Stripe call in test_full_purchase_flow?
(test code and the error attached)
Result: fixed the order of @patch arguments and the mock setup.

## 2. Test generation

_Prompt 5 — model tests_

Write pytest tests for these models using factory-boy. Cover __str__,
default values, validation and relations.
(code of books/models.py, orders/models.py, users/models.py attached)

_Prompt 6 — form and view tests_

Write pytest-django tests for these forms and views. Mock Stripe with
unittest.mock.patch and check emails with mail.outbox.
(code of forms, views, urls attached)

_Prompt 7 — fixing failing tests_

This test fails with the following error. Explain why and fix it.
(traceback attached)
Used several times (missing fields in factories, unique slug, mock argument
order, query count in the permissions page).

## 3. Documentation

_Prompt 8 — docstrings_

Add docstrings to all views in these files. Do not change the logic.
(code of books/views.py, orders/views.py, users/views.py attached)

_Prompt 9 — README_

Write a README.md for this Django bookstore project: features, structure,
how to run with Docker and locally, tests, translations, and an "AI Usage"
section.

Notes
• Every AI answer was checked by running pytest.
• Some recommendations were rejected (see AI_REVIEW.md).