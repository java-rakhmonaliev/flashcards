// ─── Theme Toggle ─────────────────────────────────────────────
const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const nextTheme = isLight ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', nextTheme);
    localStorage.setItem('theme', nextTheme);
  });
}

// ─── Tab Switching ────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(target)?.classList.add('active');
  });
});

// ─── Confirm Deletes ──────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});

// ─── Flashcard Flip ──────────────────────────────────────────
const flashcardWrapper = document.querySelector('.flashcard-wrapper');
const flashcardInner   = document.querySelector('.flashcard-inner');
const answerButtons    = document.querySelector('.answer-buttons');
const flipHint         = document.querySelector('.study-flip-hint');

if (flashcardInner) {
  let flipped = false;

  function flipCard() {
    if (flipped) return; // only flip once per card
    flipped = true;
    flashcardInner.classList.add('flipped');
    answerButtons?.classList.add('visible');
    if (flipHint) flipHint.style.display = 'none';
  }

  flashcardWrapper?.addEventListener('click', flipCard);

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.code === 'Space') {
      e.preventDefault();
      flipCard();
    }
    if (e.code === 'ArrowRight' || e.key === 'k' || e.key === 'K') {
      if (flipped) submitAnswer(true);
    }
    if (e.code === 'ArrowLeft' || e.key === 'j' || e.key === 'J') {
      if (flipped) submitAnswer(false);
    }
  });
}

// ─── Answer Submission ────────────────────────────────────────
async function submitAnswer(correct) {
  const btn = correct
    ? document.querySelector('.btn-correct')
    : document.querySelector('.btn-wrong');

  if (!btn || btn.disabled) return;

  // disable both buttons immediately
  document.querySelectorAll('.btn-correct, .btn-wrong').forEach(b => b.disabled = true);

  const cardId     = document.querySelector('[data-card-id]')?.dataset.cardId;
  const sessionPk  = document.querySelector('[data-session-pk]')?.dataset.sessionPk;
  const csrfToken  = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

  // visual feedback
  const backFace = document.querySelector('.flashcard-face.back');
  if (correct) {
    backFace?.classList.add('glow-correct');
  } else {
    backFace?.classList.add('glow-wrong');
    flashcardInner?.classList.add('shake');
    setTimeout(() => flashcardInner?.classList.remove('shake'), 400);
  }

  try {
    const res = await fetch(`/session/${sessionPk}/answer/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ card_id: parseInt(cardId), correct }),
    });

    const data = await res.json();

    setTimeout(() => {
      if (data.finished) {
        window.location.href = `/session/${sessionPk}/summary/`;
      } else {
        window.location.reload();
      }
    }, 420);

  } catch (err) {
    console.error('Answer submit failed:', err);
  }
}

document.querySelector('.btn-correct')?.addEventListener('click', () => submitAnswer(true));
document.querySelector('.btn-wrong')?.addEventListener('click', () => submitAnswer(false));