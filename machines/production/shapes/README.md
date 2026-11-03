# shapes

What this bay's model offers, one file a shape. A person sends only what the shape takes (`takes:`,
at most `limit:` characters). The prompt around it, the answer's length and the effort word are
fixed here, so a reply never carries them. Effort words map to the model's knobs in `../model.yml`.
`fcpm model shapes` lists them; `fcpm model ask "TEXT" -Shape poem` tries one. One `key: value` a line.
