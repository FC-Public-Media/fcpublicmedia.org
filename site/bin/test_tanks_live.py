"""tanks_live.py, offline: a fake worker that answers as site-worker's readAnswers does, and small built sites."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tanks_live  # noqa: E402


def fake_worker(tanks, kept):
    """readAnswers's order: tank, then each field in turn (first unknown stops it), then keep. `kept` collects keeps."""
    def post(body):
        tank = tanks.get(body["form"])
        if tank is None:
            return False, f'There is no tank "{body["form"]}".'
        answered = {}
        for key, value in body["answers"].items():
            if key == "website":
                continue
            kind = tank.get(key)
            if kind is None:
                return False, f'The {body["form"]} tank has no "{key}".'
            if kind == "list" and not isinstance(value, list):
                return False, f'"{key}" is a list of options.'
            if kind in ("text", "long") and value.strip():
                answered[key] = value
        if not answered:
            return False, "Nothing was answered."
        kept.append(body)
        return True, ""
    return post


def built(pages):
    d = pathlib.Path(tempfile.mkdtemp())
    for name, text in pages.items():
        (d / name).parent.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text)
    return d


TANKS = {"program": {"first_name": "text", "email": "text", "copyright": "yes", "topics": "list"},
         "book": {"first_name": "text", "email": "text", "space": "text", "when": "text"}}
W = 'data-worker="https://cloud.example"'


class Probe(unittest.TestCase):
    def setUp(self):
        self.kept = []
        self.post = fake_worker(TANKS, self.kept)

    def test_a_matching_form_passes_and_nothing_is_kept(self):
        self.assertEqual(tanks_live.probe(self.post, "program", {"first_name", "email", "copyright", "topics"}), ("ok",))
        self.assertEqual(self.kept, [])

    def test_a_missing_tank_is_named(self):
        self.assertEqual(tanks_live.probe(self.post, "instructor@2", {"email"}), ("no-tank",))

    def test_a_missing_field_is_named(self):
        self.assertEqual(tanks_live.probe(self.post, "program", {"email", "pronouns"}), ("no-field", "pronouns"))

    def test_an_answer_that_would_be_kept_is_never_sent(self):
        # Even a worker that kept anything answered would get only empty fields and the probe field.
        sent = []
        tanks_live.probe(lambda body: (sent.append(body), (False, 'The program tank has no "zz-tanks-live-probe".'))[1],
                         "program", {"email"})
        for body in sent:
            self.assertEqual(list(body["answers"])[-1], tanks_live.PROBE)
            self.assertTrue(all(v in ("", []) for v in body["answers"].values()))


class Forms(unittest.TestCase):
    def test_fields_come_from_the_form_and_the_trap_is_left_out(self):
        site = built({"submit/index.html": f'<form data-tank="program" {W}><input name="email">'
                                           '<input name="website"><select name="topics"></select></form>'})
        [f] = tanks_live.forms_in(site)
        self.assertEqual((f["page"], f["tank"], f["fields"]), ("/submit/index.html", "program", {"email", "topics"}))

    def test_a_field_outside_the_form_joins_it_by_id(self):
        site = built({"join/index.html": f'<form id="j" data-tank="program" {W}><input name="email"></form>'
                                         '<input form="j" name="copyright" type="checkbox">'})
        self.assertEqual(tanks_live.forms_in(site)[0]["fields"], {"email", "copyright"})

    def test_a_script_built_reply_is_checked_by_what_the_script_sends(self):
        site = built({"reserve/index.html": f'<form data-tank="book" {W}><input name="name"><input name="host"></form>',
                      "assets/js/book.js": "const answers = {};\nif (first) answers.first_name = first;\n"
                                           "answers.space = x;\nif (a.b === c) answers.when = w;\n"
                                           "const body = { form: 'book', answers };"})
        [f] = tanks_live.forms_in(site)
        self.assertEqual((f["fields"], f["sent_by"]), ({"first_name", "space", "when"}, "/assets/js/book.js"))


class TheCheckWouldNotice(unittest.TestCase):
    """2026-10-28 again: a page that sends a tank (or a field) the worker doesn't have yet stops the deploy."""

    def run_on(self, pages):
        kept = []
        results = tanks_live.check(tanks_live.forms_in(built(pages)), lambda worker: fake_worker(TANKS, kept))
        self.assertEqual(kept, [])
        return {f["page"]: v for f, v in results}

    def test_it_would_notice(self):
        got = self.run_on({
            "learn/index.html": f'<form data-tank="instructor@2" {W}><input name="email"></form>',
            "submit/index.html": f'<form data-tank="program" {W}><input name="email"><input name="pronouns"></form>',
            "join/index.html": f'<form data-tank="program" {W}><input name="email"></form>',
            "no-worker/index.html": '<form data-tank="program"><input name="email"></form>',
        })
        self.assertEqual(got["/learn/index.html"], ("no-tank",))
        self.assertEqual(got["/submit/index.html"], ("no-field", "pronouns"))
        self.assertEqual(got["/join/index.html"], ("ok",))
        self.assertEqual(got["/no-worker/index.html"][0], "odd")

    def test_unknown_answers_are_not_taken_as_a_pass(self):
        self.assertEqual(tanks_live.judge("program", "Answers come from our own pages.")[0], "odd")
        self.assertEqual(tanks_live.judge("program", 'The program tank has no "email".'), ("no-field", "email"))


if __name__ == "__main__":
    unittest.main()
