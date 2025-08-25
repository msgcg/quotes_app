from django.db import models
from django.db.models import Count

class Source(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    def get_quote_count(self):
        return self.quote_set.count()

    def has_too_many_quotes(self):
        return self.get_quote_count() >= 3

class Quote(models.Model):
    text = models.TextField()
    source = models.ForeignKey(Source, on_delete=models.CASCADE, help_text="The source of the quote.")
    weight = models.IntegerField(default=1)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    class Meta:
        unique_together = ('text', 'source')

    def __str__(self):
        return f'\"{self.text[:50]}...\" - {self.source.name}'

    def save(self, *args, **kwargs):
        if self.source.has_too_many_quotes():
            raise ValueError(f"Source '{self.source.name}' already has 3 quotes.")
        if Quote.objects.filter(text=self.text, source=self.source).exists():
            raise ValueError("Duplicate quote for this source.")
        super().save(*args, **kwargs)


class Vote(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE)
    vote = models.IntegerField()

    def __str__(self):
        return f'{self.quote.text[:50]}... - Vote: {self.vote}'
