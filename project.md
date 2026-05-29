# Flashcard App — Project Status & Build Plan

> Personal vocabulary flashcard web app built with Django + SQLite.
> Styled after Not Boring Software — interactive, game-like, satisfying.

---

## Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Django 5.x | MVT pattern, class-based views where appropriate |
| Database | SQLite | Single user, no need for Postgres |
| Frontend | Django Templates + Vanilla JS | No React, no build step |
| CSS | Custom CSS (Space Grotesk) | Loaded via Google Fonts |
| Animation | CSS 3D transforms + JS | Card flip, button press, shake effects |
| CSV Parsing | Python `csv` module | Built into stdlib, no extra dependency |

---

## Build Phases

### Phase 1 — Database Design ✅ (in progress)
> Design only. No code. No migrations.

**Models to design:**

**`Deck`**
- `id` — auto PK
- `name` — CharField
- `description` — TextField (optional)
- `created_at` — DateTimeField auto
- `updated_at` — DateTimeField auto

**`Card`**
- `id` — auto PK
- `deck` — ForeignKey → Deck (CASCADE delete)
- `front` — TextField (question / word)
- `back` — TextField (answer / translation)
- `created_at` — DateTimeField auto
- `updated_at` — DateTimeField auto

**`CardStat`**
- `id` — auto PK
- `card` — OneToOneField → Card (CASCADE delete)
- `times_seen` — IntegerField default 0
- `times_correct` — IntegerField default 0
- `times_wrong` — IntegerField default 0
- `streak` — IntegerField default 0 (consecutive correct answers)
- `mastered` — BooleanField default False (True when streak >= 3)
- `last_seen` — DateTimeField null/blank

**`StudySession`**
- `id` — auto PK
- `deck` — ForeignKey → Deck (CASCADE delete)
- `started_at` — DateTimeField auto
- `finished_at` — DateTimeField null/blank
- `total_cards` — IntegerField
- `correct_count` — IntegerField default 0
- `wrong_count` — IntegerField default 0

**Relationships summary:**
```
Deck 1──∞ Card 1──1 CardStat
Deck 1──∞ StudySession
```

**Key decisions:**
- `CardStat` is auto-created via Django signal when a `Card` is saved
- Mastered threshold: streak >= 3 correct in a row
- Deleting a deck cascades and deletes all cards, stats, and sessions
- No auth model — single user app

---

### Phase 2 — Django Config & Core App ⬜
> Scaffold the project, wire up URLs, configure settings, create models + migrations.

**Steps:**
- `django-admin startproject config .`
- `python manage.py startapp flashcards`
- Settings: `INSTALLED_APPS`, `TEMPLATES`, `STATIC_URL`, `MEDIA_ROOT`
- `models.py` — implement all 4 models from Phase 1
- `signals.py` — auto-create `CardStat` on `Card` post_save
- `admin.py` — register all models for sanity checking
- `python manage.py makemigrations && migrate`

**Project structure:**
```
flashcard_app/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── flashcards/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── signals.py
│   ├── admin.py
│   └── templates/
│       └── flashcards/
│           ├── base.html
│           ├── deck_list.html
│           ├── deck_detail.html
│           ├── study_session.html
│           └── session_summary.html
├── static/
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── main.js
├── db.sqlite3
└── manage.py
```

---

### Phase 3 — Logic (Views & Business Rules) ⬜
> All backend logic. No templates yet — test via Django admin or shell.

**URLs & Views to build:**

| URL | View | Purpose |
|---|---|---|
| `/` | `DeckListView` | Show all decks |
| `/deck/create/` | `DeckCreateView` | Create new deck |
| `/deck/<id>/` | `DeckDetailView` | Cards in a deck, edit/delete |
| `/deck/<id>/edit/` | `DeckUpdateView` | Rename deck |
| `/deck/<id>/delete/` | `DeckDeleteView` | Delete deck + cascade |
| `/deck/<id>/import/` | `CSVImportView` | Upload CSV → bulk create cards |
| `/deck/<id>/study/` | `StudySessionView` | Start/continue a study session |
| `/card/create/<deck_id>/` | `CardCreateView` | Add single card to deck |
| `/card/<id>/edit/` | `CardUpdateView` | Edit card front/back |
| `/card/<id>/delete/` | `CardDeleteView` | Delete single card |
| `/session/<id>/result/` | `SessionSummaryView` | Show session results |
| `/api/card/<id>/answer/` | `CardAnswerView` | AJAX — submit correct/wrong |

**CSV Import logic:**
- Accept `.csv` file upload
- Expected format: `front,back` (with or without header row)
- Strip whitespace from each field
- Skip blank rows
- Bulk create cards via `Card.objects.bulk_create()`
- Flash message: "X cards imported successfully"

**Study session logic:**
- On session start: fetch all non-mastered cards, shuffle them
- Store card order in Django session (`request.session`)
- On each answer: call `CardAnswerView` via AJAX → update `CardStat`
- Missed cards get appended to the back of the queue for the same session
- Session ends when queue is empty
- On end: set `StudySession.finished_at`, calculate final counts

**Mastered logic (in `CardStat`):**
```python
def mark_correct(self):
    self.times_correct += 1
    self.times_seen += 1
    self.streak += 1
    if self.streak >= 3:
        self.mastered = True
    self.save()

def mark_wrong(self):
    self.times_wrong += 1
    self.times_seen += 1
    self.streak = 0
    self.mastered = False
    self.save()
```

---

### Phase 4 — Templates & UI ⬜
> Build all HTML templates + CSS + JS. Not Boring Software aesthetic.

**Design system:**

```css
/* Fonts */
font-family: 'Space Grotesk', sans-serif;
/* Bold (700) — deck names, score, card word */
/* Medium (500) — buttons, labels */
/* Regular (400) — body, descriptions */
/* Light (300) — metadata, timestamps */

/* Colors */
--bg: #0D0D0F;
--surface: #16161A;
--surface-raised: #1E1E24;
--border: #2A2A35;
--accent: #6C63FF;       /* primary actions */
--accent-hover: #8B85FF;
--correct: #22C55E;
--wrong: #EF4444;
--text-primary: #F0F0F5;
--text-secondary: #8888A0;
--text-muted: #55556A;
```

**Card flip (CSS + JS):**
```css
.card-container { perspective: 1000px; }
.card-inner {
  transform-style: preserve-3d;
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-inner.flipped { transform: rotateY(180deg); }
.card-front, .card-back { backface-visibility: hidden; }
.card-back { transform: rotateY(180deg); }
```

**Micro-interactions:**
- Button press: `transform: scale(0.96)` on `:active`
- Correct answer: green glow pulse on card edge
- Wrong answer: horizontal shake animation (keyframes)
- Deck tile hover: `translateY(-3px)` + stronger shadow

**Keyboard shortcuts (JS):**
- `Space` — flip card
- `→` or `K` — got it (correct)
- `←` or `J` — missed it (wrong)

**Templates to build:**
- `base.html` — font import, CSS, JS, nav
- `deck_list.html` — deck tiles, create button
- `deck_detail.html` — card table, import CSV form, add card form
- `study_session.html` — card flip UI, progress bar, keyboard shortcuts
- `session_summary.html` — score, missed words list, action buttons

---

### Phase 5 — Testing ⬜
> Manual + basic Django test cases.

**What to test:**

- [ ] Create deck → appears on home page
- [ ] Import CSV → correct number of cards created
- [ ] Import CSV with bad format → graceful error, no crash
- [ ] Add / edit / delete single card
- [ ] Study session: cards cycle correctly, missed cards re-queue
- [ ] `CardStat` updates correctly on correct/wrong answer
- [ ] Streak hits 3 → card marked mastered
- [ ] Mastered cards skipped in next session
- [ ] Session summary shows correct score and missed words
- [ ] "Study missed only" re-runs with only wrong cards
- [ ] Delete deck → cascades cleanly, no orphaned records
- [ ] Keyboard shortcuts work on study screen
- [ ] Card flip animation works and doesn't break on fast clicks

---

## Current Status

| Phase | Status |
|---|---|
| Phase 1 — DB Design | 🔄 In Progress |
| Phase 2 — Django Config | ⬜ Not Started |
| Phase 3 — Logic | ⬜ Not Started |
| Phase 4 — Templates & UI | ⬜ Not Started |
| Phase 5 — Testing | ⬜ Not Started |
