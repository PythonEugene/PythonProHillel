from django.db import models
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    author = models.CharField(max_length=100, verbose_name=_("Author"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Price"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    stock = models.PositiveIntegerField(default=0, verbose_name=_("Stock"))
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
        related_name="books"
    )
    class Meta:
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        return self.title