# models

Bay 1's spread: stock models, as their labs published them, with no harness of ours around them. They are
research stock for testing hypotheses: which model, or which size, can do a given job by default. None of
them is a final model. One file a model, `key: value` a line, pinned by its sha256 and its size.
There is no default model.

The spread is what can be up, never what must be. Which models are up is bay 1's own choice, kept on
the bay (`up`, beside the server), and it changes as often as the testing does: `fcpm model pick` is a
list to toggle with the space bar, and `fcpm model pick qwen3.5-9b,gpt-oss-20b` says it in one line.
Nothing is up until it is picked, and any model may be taken down, so a bigger one can have the whole
card. A request that names no model gets one that is up and loaded, else the first that is up, and the
answer names it. Picking a model fetches it if it isn't here yet (all nine come to about 77 GB), and a
running server takes the new line-up at once. `fcpm model on` serves the models that are up on the same
port as a router: a request names its model, the router loads it, and when room is needed the one asked
least lately leaves. `fcpm model models` lists them, placed and loaded. What the running server lists
is what has joined: digitization's `asks` reads it into `asks/state.json`, and qr.local's screen shows
those names under its inbox bar, a loaded one bright.

The card is an RTX 4080 with 16 GB, beside 32 GB of memory. A model bigger than the card keeps part of
itself in memory and answers more slowly; llama.cpp decides how much goes where (`--fit`), and every
model has the same 32k context (`../model.yml`), the advocate engine's floor.

## The spread

| model | lab | size | in it to answer |
|---|---|---|---|
| `qwen3.5-0.8b` | Qwen | 0.8B | the ladder's floor: phone-sized, where the label reducer wants to end up |
| `qwen3.5-2b` | Qwen | 2B | the ladder's second rung |
| `qwen3.5-4b` | Qwen | 4B | the waterline: what the shapes were first asked on |
| `qwen3.5-9b` | Qwen | 9B | the ladder's top rung that sits on the card whole |
| `qwen3.8-27b` | Qwen | 27B | the newest Qwen, dense, the most the card brings; the slow one |
| `gemma-4-12b` | Google | 12B | another lab beside the 9B rung, quantized by Google itself |
| `gemma-4-26b-a4b` | Google | 26B, 4B at work | mixture of experts: does a task need knowledge or width |
| `gpt-oss-20b` | OpenAI | 21B, 3.6B at work | mixture of experts that always reasons, by a level, never off |
| `granite-4.2-8b` | IBM | 8B | a third lab at the 8B rung, trained for business work and tool calls |

The Qwen 3.5 ladder holds the family still and moves only the size, so a threshold found on it is about
size. The other labs sit beside its rungs, so a threshold that holds across them is not one lab's
training. All nine are Apache-2.0 and ungated. Each file came from the lab's own repository or a
quantizer the community checks (lmstudio-community, ggml-org); the sha256 is Hugging Face's own.

Thinking: each lab's chat template takes `enable_thinking`, and our effort words map to it in
`../model.yml` (quick: off; considered: a budget). gpt-oss can't stop reasoning, so its file says
`thinking: effort` and what each word is to it (quick: low; considered: medium), and it always gets
room to think before it answers.

## Judging

`machines/digitization/spread "TEXT" [--shape NAME]` asks every joined model the same words with the
same seed, one at a time, and keeps the round in `~/fcpm/spread/<when>/` (`round.md` to read,
`round.json` for the record). Nothing scores it: a person reads the round and says which answers
are good enough. That is how a job learns which models can be trusted with it.

## Adding or dropping one

A new file here (its `source`, `size` and `sha256` read from Hugging Face's API, never typed); on bay
1 it can then be picked. Dropping one is deleting its file here; the weights stay in the store until
someone deletes them there.

`bin/test_model_ps1.py` runs model.ps1's own functions (the line-up, the presets, the picker) under
PowerShell 7 on digitization; what needs Windows is proved on bay 1.
