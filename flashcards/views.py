import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Deck, Card, CardStat, StudySession
from .forms import DeckForm, CardForm, CSVImportForm


# ─── Deck Views ───────────────────────────────────────────────────────────────

def deck_list(request):
    decks = Deck.objects.all()
    return render(request, 'flashcards/deck_list.html', {'decks': decks})


def deck_create(request):
    if request.method == 'POST':
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save()
            messages.success(request, f'Deck "{deck.name}" created.')
            return redirect('deck_detail', pk=deck.pk)
    else:
        form = DeckForm()
    return render(request, 'flashcards/deck_form.html', {'form': form, 'action': 'Create'})


def deck_detail(request, pk):
    deck = get_object_or_404(Deck, pk=pk)
    cards = deck.cards.select_related('stat').all()
    card_form = CardForm()
    csv_form = CSVImportForm()
    return render(request, 'flashcards/deck_detail.html', {
        'deck': deck,
        'cards': cards,
        'card_form': card_form,
        'csv_form': csv_form,
    })


def deck_edit(request, pk):
    deck = get_object_or_404(Deck, pk=pk)
    if request.method == 'POST':
        form = DeckForm(request.POST, instance=deck)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deck updated.')
            return redirect('deck_detail', pk=deck.pk)
    else:
        form = DeckForm(instance=deck)
    return render(request, 'flashcards/deck_form.html', {'form': form, 'action': 'Edit', 'deck': deck})


@require_POST
def deck_delete(request, pk):
    deck = get_object_or_404(Deck, pk=pk)
    name = deck.name
    deck.delete()
    messages.success(request, f'Deck "{name}" deleted.')
    return redirect('deck_list')


# ─── Card Views ───────────────────────────────────────────────────────────────

@require_POST
def card_create(request, deck_pk):
    deck = get_object_or_404(Deck, pk=deck_pk)
    form = CardForm(request.POST)
    if form.is_valid():
        card = form.save(commit=False)
        card.deck = deck
        card.save()
        messages.success(request, 'Card added.')
    else:
        messages.error(request, 'Invalid card data.')
    return redirect('deck_detail', pk=deck.pk)


def card_edit(request, pk):
    card = get_object_or_404(Card, pk=pk)
    if request.method == 'POST':
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, 'Card updated.')
            return redirect('deck_detail', pk=card.deck.pk)
    else:
        form = CardForm(instance=card)
    return render(request, 'flashcards/card_form.html', {'form': form, 'card': card})


@require_POST
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk)
    deck_pk = card.deck.pk
    card.delete()
    messages.success(request, 'Card deleted.')
    return redirect('deck_detail', pk=deck_pk)


# ─── CSV Import ───────────────────────────────────────────────────────────────

@require_POST
def csv_import(request, deck_pk):
    deck = get_object_or_404(Deck, pk=deck_pk)
    form = CSVImportForm(request.POST, request.FILES)
    if form.is_valid():
        pairs = form.get_cards()
        if not pairs:
            messages.error(request, 'No valid rows found in CSV.')
            return redirect('deck_detail', pk=deck.pk)
        Card.objects.bulk_create([
            Card(deck=deck, front=front, back=back)
            for front, back in pairs
        ])
        # bulk_create skips signals so we manually create stats
        cards_without_stat = deck.cards.filter(stat__isnull=True)
        CardStat.objects.bulk_create([
            CardStat(card=card) for card in cards_without_stat
        ])
        messages.success(request, f'{len(pairs)} cards imported successfully.')
    else:
        messages.error(request, 'Invalid file. Please upload a .csv file.')
    return redirect('deck_detail', pk=deck.pk)


# ─── Study Session Views ───────────────────────────────────────────────────────

def study_session_start(request, deck_pk):
    deck = get_object_or_404(Deck, pk=deck_pk)
    cards = list(deck.cards.select_related('stat').filter(stat__mastered=False))

    if not cards:
        # all mastered — offer to reset
        messages.info(request, 'All cards mastered! Reset to study again.')
        return redirect('deck_detail', pk=deck.pk)

    random.shuffle(cards)
    session = StudySession.objects.create(
        deck=deck,
        total_cards=len(cards),
    )
    # randomly flip half the cards so mixed direction is built into the queue
    queue = [{'id': c.pk, 'flipped': random.choice([True, False])} for c in cards]
    request.session[f'study_{session.pk}'] = {
        'queue': queue,
        'wrong_ids': [],
        'correct_ids': [],
        'current_index': 0,
        'phase': 'main',
    }
    return redirect('study_session', session_pk=session.pk)


def study_session(request, session_pk):
    session = get_object_or_404(StudySession, pk=session_pk)
    state = request.session.get(f'study_{session_pk}')

    if not state or session.is_finished:
        return redirect('session_summary', session_pk=session_pk)

    queue = state['queue']
    current_index = state['current_index']

    if current_index >= len(queue):
        return _finish_session(request, session, state)

    current_item = queue[current_index]
    # support both old format (int) and new format (dict)
    if isinstance(current_item, dict):
        card_id = current_item['id']
        flipped = current_item['flipped']
    else:
        card_id = current_item
        flipped = False

    current_card = get_object_or_404(Card, pk=card_id)
    total = len(queue)
    progress_percent = round((current_index / total) * 100) if total > 0 else 0

    # determine what to show on front vs back
    if flipped:
        show_front = current_card.back
        show_back = current_card.front
        front_label = 'Translation'
        back_label = current_card.deck.name
    else:
        show_front = current_card.front
        show_back = current_card.back
        front_label = current_card.deck.name
        back_label = 'Translation'

    return render(request, 'flashcards/study_session.html', {
        'session': session,
        'card': current_card,
        'show_front': show_front,
        'show_back': show_back,
        'front_label': front_label,
        'back_label': back_label,
        'current_index': current_index + 1,
        'total': total,
        'progress_percent': progress_percent,
        'correct_count': len(state['correct_ids']),
        'wrong_count': len(state['wrong_ids']),
    })


@require_POST
def card_answer(request, session_pk):
    session = get_object_or_404(StudySession, pk=session_pk)
    state = request.session.get(f'study_{session_pk}')

    if not state:
        return JsonResponse({'error': 'Session not found'}, status=404)

    data = json.loads(request.body)
    card_id = data.get('card_id')
    correct = data.get('correct')  # bool

    card = get_object_or_404(Card, pk=card_id)
    stat = card.stat

    if correct:
        stat.mark_correct()
        state['correct_ids'].append(card_id)
        session.correct_count += 1
    else:
        stat.mark_wrong()
        state['wrong_ids'].append(card_id)
        session.wrong_count += 1
        state['queue'].append({'id': card_id, 'flipped': random.choice([True, False])})  # re-queue at end

    session.save()
    state['current_index'] += 1
    request.session[f'study_{session_pk}'] = state
    request.session.modified = True

    queue = state['queue']
    current_index = state['current_index']
    finished = current_index >= len(queue)

    return JsonResponse({
        'finished': finished,
        'correct_count': len(state['correct_ids']),
        'wrong_count': len(state['wrong_ids']),
    })


def _finish_session(request, session, state):
    session.finished_at = timezone.now()
    session.save()
    del request.session[f'study_{session.pk}']
    return redirect('session_summary', session_pk=session.pk)


def session_summary(request, session_pk):
    session = get_object_or_404(StudySession, pk=session_pk)

    # if not finished yet, finish it
    if not session.is_finished:
        session.finished_at = timezone.now()
        session.save()

    wrong_card_ids = request.session.get(f'wrong_summary_{session_pk}', [])

    # get missed cards from session stats
    missed_cards = Card.objects.filter(
        deck=session.deck,
        stat__times_seen__gt=0,
    ).select_related('stat')

    return render(request, 'flashcards/session_summary.html', {
        'session': session,
        'missed_cards': missed_cards.filter(stat__streak=0),
    })


def deck_reset(request, pk):
    deck = get_object_or_404(Deck, pk=pk)
    if request.method == 'POST':
        CardStat.objects.filter(card__deck=deck).update(
            streak=0, mastered=False, times_seen=0,
            times_correct=0, times_wrong=0, last_seen=None
        )
        messages.success(request, f'All progress reset for "{deck.name}".')
    return redirect('deck_detail', pk=pk)