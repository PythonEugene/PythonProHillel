# AI Code Review — DjangoBookStore

This document describes the AI-assisted code review of three complex views
of the DjangoBookStore project. For each view: the original code, the AI
recommendations, which recommendations were applied or rejected (and why),
and the final code.

AI used: Claude. The prompts are listed in `AI_PROMPTS.md`.


## View 1: `order_success` (orders/views.py)

**Prompt used:** "Do a code review of this Django view. Look for security
problems, bugs and bad practices."

### Original code

```python
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = Order.OrderStatus.PAID
    order.save(update_fields=['status'])
    return render(request, 'orders/success_order.html', {'order': order})
```

### AI recommendations

1. **Critical (security):** the order is marked `PAID` just by opening the
 URL. No payment is verified, so anyone can "pay" any order by opening
 `/orders/<id>/success/` (ids are easy to guess).
2. Verify the payment with Stripe (`Session.retrieve`, `payment_status == 'paid'`)
 before changing the status.
3. Change the status only if the order is still `PENDING`, so paid or
 canceled orders are not overwritten.

### Applied / rejected

| Recommendation | Decision | Reason |
|---|---|---|
| 1. Do not mark PAID on visit | Applied | Real security hole |
| 2. Verify payment via Stripe | Applied | Source of truth is Stripe |
| 3. Only update PENDING orders | Applied | Prevents status regressions |

### Final code

```python
def order_success(request, order_id):
    """Show the "payment successful" page.

    The order status is changed to PAID only if Stripe confirms the payment.
    """
    order = get_object_or_404(Order, id=order_id)

    if order.status == Order.OrderStatus.PENDING and order.stripe_checkout_id:
        session = stripe.checkout.Session.retrieve(order.stripe_checkout_id)
        if session.payment_status == 'paid':
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=['status'])

    return render(request, 'orders/success_order.html', {'order': order})
```

### Tests affected

Two existing tests expected `PAID` without Stripe and failed after the fix
(`test_order_success_marks_paid`, `test_full_purchase_flow`). They were
updated to mock `Session.retrieve`, and a new test
`test_order_success_not_paid_keeps_pending` proves that an unpaid order
stays `PENDING`.

---

## View 2: `stripe_webhook` (orders/views.py)

**Prompt used:** "Review this Stripe webhook view for Django. What can break
in production?"

### Original code

```python
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata']['order_id']
        with transaction.atomic():
            order = get_object_or_404(Order, id=order_id)
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=['status'])

    return HttpResponse(status=200)
```

### AI recommendations

1. **Critical:** no `@csrf_exempt`. Django rejects POST requests without a
 CSRF token, and Stripe does not send one, so every real webhook would get
 403 and no order would ever become PAID. Django's test client skips CSRF
 checks, so the existing tests could not detect this.
2. Add `@require_POST`, so the endpoint does not run on GET requests.
3. `stripe.error.SignatureVerificationError` is outdated: `stripe.error`
 was removed in newer library versions. Use `stripe.SignatureVerificationError`.
4. Make the handler idempotent: Stripe may deliver the same event several
 times. Update only orders that are still `PENDING`.
5. Use `select_for_update()` so two simultaneous deliveries of the same
 event do not race.
6. If the order does not exist, do not raise 404 (Stripe would retry for
 days). Log a warning and return 200.

### Applied / rejected

| Recommendation | Decision | Reason |
|---|---|---|
| 1. `@csrf_exempt` | Applied | Without it the webhook never works |
| 2. `@require_POST` | Applied | Only POST is valid for webhooks |
| 3. `stripe.SignatureVerificationError` | Applied | `stripe.error` is removed in new versions |
| 4. Idempotency (only PENDING) | Applied | Repeated events must be harmless |
| 5. `select_for_update()` | Applied | Cheap protection; ignored by SQLite, works on PostgreSQL |
| 6. Unknown order: log and 200 | Applied | Avoids endless retries from Stripe |

### Final code

```python
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Receive Stripe notifications and mark the order as paid.

    The request signature is verified with the webhook secret. Only the
    checkout.session.completed event is handled; repeated deliveries are safe.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
    order_id = event['data']['object']['metadata']['order_id']
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(id=order_id).first()
        if order is None:
            logger.warning('Webhook for unknown order %s', order_id)
        elif order.status == Order.OrderStatus.PENDING:
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=['status'])

    return HttpResponse(status=200)
```

### Tests added

- `test_webhook_get_not_allowed` (405 on GET)
- `test_webhook_requires_no_csrf_token` (client with `enforce_csrf_checks=True`
 gets past CSRF and reaches signature verification)
- `test_webhook_unknown_order_returns_200`
- `test_webhook_repeat_does_not_change_canceled_order`

---

## View 3: `ManagerUserPermissionsView` (users/views.py)

**Prompt used:** "Review this Django class-based view and its form. Look for
performance problems, security and readability."

### Original code

```python
class PermissionManagementService:
    @staticmethod
    def update_user_permissions(user, permission_ids):
        user.user_permissions.clear()
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)


class ManagerUserPermissionsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'permissions_management.html'
    form_class = UserPermissionForm

    def test_func(self) -> bool | None:
        return self.request.user.has_perm('users.can_see_user_permissions')

    def handle_no_permission(self):
        return HttpResponseForbidden('Have no access to requested page')

    def get_target_user(self):
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
        'user': self.get_target_user(),
        'manager': self.request.user
        })
        return kwargs

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.get_target_user()
        return context

    def get_success_url(self) -> str:
        return reverse_lazy('manage_permissions', kwargs={'user_id': self.kwargs['user_id']})

    def form_valid(self, form: Any):
        selected_permissions = form.cleaned_data.get('permissions', [])
        target_user = self.get_target_user()

        PermissionManagementService.update_user_permissions(
            target_user,
            selected_permissions
        )
        return super().form_valid(form)
```

Related code in `users/forms.py` (`UserPermissionForm.__init__`):

```python
permissions = Permission.objects.all()
self.fields['permissions'].choices = [
    (perm.id, f'{perm.content_type.app_label}.{perm.codename} - {perm.name}')
    for perm in permissions.order_by('content_type__app_label', 'codename')
]
```

### AI recommendations

1. `get_target_user()` is called 3 times per request, which means 3
 identical SQL queries. Cache the result (`cached_property`).
2. `clear()` before `set()` is redundant: `set()` already replaces all
 permissions.
3. `get_success_url` uses `'manage_permissions'` without the `users:`
 namespace, so after saving the form it raises `NoReverseMatch`.
4. `form_valid` does not check `can_set_user_permissions`. Protection relies
 only on the form field being `disabled`, which is implicit and fragile.
 Add an explicit check.
5. N+1 queries in the form: `perm.content_type` is loaded separately for
 every permission (about 45 extra queries). Use `select_related('content_type')`.
6. A manager can grant permissions to themselves (privilege escalation).

### Applied / rejected

| Recommendation | Decision | Reason |
|---|---|---|
| 1. Cache target user | Applied | 3 queries become 1 |
| 2. Remove `clear()` | Applied | Redundant |
| 3. Fix namespace in `get_success_url` | Applied | Real bug, found by integration test |
| 4. Explicit permission check in `form_valid` | Applied | Defense in depth |
| 5. `select_related` in the form | Applied | Removes the N+1 problem |
| 6. Forbid editing own permissions | Rejected | Out of scope for this learning project; in a real project it would be forbidden |

### Final code

`users/views.py`:

```python
from django.utils.functional import cached_property


class PermissionManagementService:
    @staticmethod
    def update_user_permissions(user, permission_ids):
    """Replace all permissions of the user with the selected ones."""
    user.user_permissions.set(Permission.objects.filter(id__in=permission_ids))


class ManagerUserPermissionsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Page for managing the permissions of a user.

    Viewing requires the can_see_user_permissions permission,
    changing requires can_set_user_permissions.
    """
    template_name = 'permissions_management.html'
    form_class = UserPermissionForm

    def test_func(self):
        return self.request.user.has_perm('users.can_see_user_permissions')

    def handle_no_permission(self):
        return HttpResponseForbidden('Have no access to requested page')

    @cached_property
    def target_user(self):
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.target_user, 'manager': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.target_user
        return context

    def get_success_url(self):
        return reverse_lazy('users:manage_permissions', kwargs={'user_id': self.kwargs['user_id']})

    def form_valid(self, form):
        if not self.request.user.has_perm('users.can_set_user_permissions'):
            return HttpResponseForbidden('No permission to change permissions')
        PermissionManagementService.update_user_permissions(
            self.target_user, form.cleaned_data.get('permissions', []))
        return super().form_valid(form)
```

`users/forms.py`:

```python
permissions = Permission.objects.select_related('content_type').order_by(
    'content_type__app_label', 'codename')
self.fields['permissions'].choices = [
    (perm.id, f'{perm.content_type.app_label}.{perm.codename} - {perm.name}')
    for perm in permissions
]
```

### Tests added

- `test_permissions_page_opens_for_viewer`
- `test_permissions_unknown_user_404`
- `test_viewer_cannot_change_permissions` (403, nothing saved)
- `test_permissions_are_replaced_not_added`
- `test_permissions_page_query_count` (guards against the N+1 problem)

---

## Conclusions

- AI found one critical security bug (`order_success`) and one production
 bug that tests could not see (missing CSRF exemption in the webhook).
- Not every recommendation was accepted: the privilege-escalation advice was
 rejected as out of scope. Every applied change was verified by tests.
- Several existing tests had to be changed after the fixes, which confirms
 that the tests really check the behavior.