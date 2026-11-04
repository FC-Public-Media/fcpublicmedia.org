# shapes

What this bay's model offers, one file a shape. A person sends only what the shape takes (`takes:`,
at most `limit:` characters). The prompt around it, the answer's length and the effort word are
fixed here, so a reply never carries them. Effort words map to the model's knobs in `../model.yml`.
`fcpm model shapes` lists them; `fcpm model ask "TEXT" -Shape poem` tries one. One `key: value` a line.

`context:` is what a shape remembers: `none` (the input is the whole scope) or `shared` (one context
for the shape, named by `context-name:`; the guestbook). A shared shape's `role:` is said first, then
a roster made from its log, then its last `sees-turns:` turns within `sees-days:`. `fcpm model
contexts` lists what is kept, each by its address (production/guestbook).
