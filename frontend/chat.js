// ─── Chat.js — ClassLogger AI Frontend Logic ─────────────────────────────────
// Handles: welcome screen, session divider, user/AI message rendering,
//          thinking indicator, markdown rendering, textarea auto-resize,
//          keyboard shortcuts, and backend fetch.

'use strict';

// ─── Configuration ───────────────────────────────────────────────────────────
// When running locally via server.py, API_BASE is empty (same-origin).
// For GitHub Pages, set this to your deployed backend URL
// e.g. 'https://classlogger-api.onrender.com'
const API_BASE =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'
    ? ''
    : '';   // ← set your deployed backend URL here for GitHub Pages

// ─── State ───────────────────────────────────────────────────────────────────
let messageCount = 0;
let isWaiting    = false;

// ─── DOM References ───────────────────────────────────────────────────────────
const thread  = document.getElementById('thread');
const input   = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');

// ─── Utilities ────────────────────────────────────────────────────────────────

/**
 * Escape raw text for safe HTML insertion.
 */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Minimal Markdown renderer.
 * Handles: fenced code blocks, inline code, **bold**, newlines.
 */
function renderMarkdown(text) {
  return escapeHtml(text)
    // Fenced code blocks  ```...```
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    // Inline code  `...`
    .replace(/`([^`\n]+)`/g, '<code>$1</code>')
    // Bold  **...**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Newlines → <br>
    .replace(/\n/g, '<br>');
}

/**
 * Current time formatted as 10:42 AM (locale-aware).
 */
function nowTime() {
  return new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Auto-resize textarea from 1 row up to 140px.
 */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

/**
 * Scroll thread to the very bottom.
 */
function scrollToBottom() {
  thread.scrollTop = thread.scrollHeight;
}

// ─── Welcome Screen ───────────────────────────────────────────────────────────

/**
 * Fade and remove the welcome state element on first send.
 */
function removeWelcome() {
  const w = document.getElementById('welcome');
  if (!w) return;
  w.style.transition = 'opacity 0.2s';
  w.style.opacity    = '0';
  setTimeout(() => w.remove(), 200);
}

/**
 * Suggestion chip — immediately send the chip's text as a message.
 */
function sendChip(el) {
  if (isWaiting) return;
  input.value = el.textContent.trim();
  autoResize(input);
  sendMessage();
}

// ─── Session Divider ──────────────────────────────────────────────────────────

/**
 * Insert a session divider before the first message of this page load.
 */
function addSessionLabel() {
  if (messageCount !== 0) return;
  const now = new Date().toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  const label = document.createElement('div');
  label.className   = 'session-label';
  label.textContent = `Session started · ${now}`;
  thread.appendChild(label);
}

// ─── Message Rendering ────────────────────────────────────────────────────────

/**
 * Append a user message bubble to the thread.
 */
function appendUser(text) {
  const row = document.createElement('div');
  row.className = 'msg user';
  row.innerHTML = `
    <div class="avatar user-av" aria-hidden="true">U</div>
    <div class="bubble" role="article" aria-label="Your message">${renderMarkdown(text)}</div>
  `;
  thread.appendChild(row);
  scrollToBottom();
}

/**
 * Append a thinking indicator row. Returns the row element.
 */
function appendThinking() {
  const row = document.createElement('div');
  row.className = 'msg ai';
  row.id        = 'thinking-row';
  row.setAttribute('aria-live', 'polite');
  row.setAttribute('aria-label', 'ClassLogger AI is thinking');
  row.innerHTML = `
    <div class="avatar ai" aria-hidden="true">AI</div>
    <div class="thinking-bubble" role="status">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  `;
  thread.appendChild(row);
  scrollToBottom();
  return row;
}

/**
 * Replace the thinking row with the final AI response.
 *
 * @param {string}  responseText — answer text (or error message)
 * @param {boolean} isError      — render as error bubble if true
 */
function resolveThinking(responseText, isError = false) {
  const row = document.getElementById('thinking-row');
  if (!row) return;
  row.removeAttribute('id');
  row.removeAttribute('aria-live');
  row.removeAttribute('aria-label');

  const bubbleClass = isError ? 'bubble error' : 'bubble';
  const content     = isError
    ? `<pre>${escapeHtml(responseText)}</pre>`
    : renderMarkdown(responseText);

  row.innerHTML = `
    <div class="avatar ai" aria-hidden="true">AI</div>
    <div>
      <div class="${bubbleClass}" role="article" aria-label="ClassLogger AI response">${content}</div>
      <div class="meta">
        <span>${nowTime()}</span>
      </div>
    </div>
  `;
  scrollToBottom();
}

// ─── Backend Integration ──────────────────────────────────────────────────────

/**
 * POST the user query to the backend and return the response.
 *
 * Expected response shape from server.py:
 *   { "answer": "string", "is_error": false }
 */
async function fetchAnswer(query) {
  const response = await fetch(`${API_BASE}/api/query`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ query }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => response.statusText);
    throw new Error(`HTTP ${response.status}: ${text}`);
  }

  return response.json();
}

// ─── Send Flow ────────────────────────────────────────────────────────────────

/**
 * Main send handler. Reads the textarea, renders the user bubble,
 * shows thinking state, calls fetchAnswer, then resolves the response.
 */
async function sendMessage() {
  const text = input.value.trim();
  if (!text || isWaiting) return;

  // Dismiss welcome state on first send
  removeWelcome();
  addSessionLabel();

  // Reset input
  input.value        = '';
  input.style.height = 'auto';

  // Lock UI
  isWaiting        = true;
  sendBtn.disabled = true;
  messageCount++;

  appendUser(text);
  appendThinking();

  try {
    const data = await fetchAnswer(text);
    resolveThinking(data.answer, data.is_error);
  } catch (err) {
    // Network or server error — render as error bubble
    resolveThinking(
      `Failed to reach the backend.\n\n${err.message}`,
      true
    );
  } finally {
    isWaiting        = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

// ─── Keyboard Handler ─────────────────────────────────────────────────────────
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ─── Expose to Global (needed for inline handlers) ───────────────────────────
window.sendChip    = sendChip;
window.sendMessage = sendMessage;
window.handleKey   = handleKey;
window.autoResize  = autoResize;
