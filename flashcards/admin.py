from django.contrib import admin
from .models import Deck, Card, CardStat, StudySession


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'card_count', 'created_at', 'updated_at']
    search_fields = ['name']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['front', 'back', 'deck', 'created_at']
    list_filter = ['deck']
    search_fields = ['front', 'back']


@admin.register(CardStat)
class CardStatAdmin(admin.ModelAdmin):
    list_display = ['card', 'times_seen', 'times_correct', 'streak', 'mastered']
    list_filter = ['mastered']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['deck', 'started_at', 'finished_at', 'correct_count', 'wrong_count', 'total_cards']
    list_filter = ['deck']