# `site/assets/js/classmode.js`

Moved out of the file. Unreviewed.

## 1

Above `import { readConfig, pickSession, clockTime, watch } from './classes.js';`

Class mode on the homepage.

The homepage has no job here beyond decorating the panel that already holds
the QR and the check-in link. It does not encode the class into anything —
the link is the same permanent /check-in/ either way, and that page works
out for itself that a class is on. One source of truth, in classes.js.

## 2

Above `el('[data-class-join]').textContent = session.running`

Deliberately not "?reason=Class". The check-in page reaches the same
conclusion from the same data, so putting it in the URL would create a
second place for the answer to live — and a link that could be shared
hours later still claiming a class is on.
