from django.db import models
from django.utils import timezone


class Deck(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def card_count(self):
        return self.cards.count()

    @property
    def mastered_count(self):
        return CardStat.objects.filter(card__deck=self, mastered=True).count()

    @property
    def progress_percent(self):
        total = self.card_count
        if total == 0:
            return 0
        return round((self.mastered_count / total) * 100)


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards')
    front = models.TextField()
    back = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.front} → {self.back}"


class CardStat(models.Model):
    card = models.OneToOneField(Card, on_delete=models.CASCADE, related_name='stat')
    times_seen = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)
    times_wrong = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    mastered = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Stat: {self.card.front}"

    def mark_correct(self):
        self.times_correct += 1
        self.times_seen += 1
        self.streak += 1
        self.last_seen = timezone.now()
        if self.streak >= 3:
            self.mastered = True
        self.save()

    def mark_wrong(self):
        self.times_wrong += 1
        self.times_seen += 1
        self.streak = 0
        self.mastered = False
        self.last_seen = timezone.now()
        self.save()

    @property
    def accuracy(self):
        if self.times_seen == 0:
            return 0
        return round((self.times_correct / self.times_seen) * 100)


class StudySession(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_cards = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Session: {self.deck.name} @ {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def score_percent(self):
        if self.total_cards == 0:
            return 0
        return round((self.correct_count / self.total_cards) * 100)

    @property
    def is_finished(self):
        return self.finished_at is not None