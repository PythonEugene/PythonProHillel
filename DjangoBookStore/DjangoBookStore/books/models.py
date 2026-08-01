from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=100, verbose_name="Title")
    author = models.CharField(max_length=100, verbose_name="Author")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    description = models.TextField(blank=True, verbose_name="Description")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock")
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.CASCADE,
        verbose_name="Category",
        related_name="books"
    )
    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"

    def __str__(self):
        return self.title