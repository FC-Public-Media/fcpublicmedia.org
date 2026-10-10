# `site/_includes/countdown.html`

Moved out of the file. Unreviewed.

## 1

Above `<p class="countdown-wrap" role="status" aria-live="polite">`

The wait before media starts.

role="status" with a live region, because the plate is decorative to a
screen reader and "Loading" is the only part of this that carries meaning.
The text is visually hidden rather than absent — a spinner with no
accessible name is a silence, and somebody waiting deserves to be told
they are waiting.

Usage:
{% raw %}{% include countdown.html label="Loading the archive" %}{% endraw %}
