#!/usr/bin/env python3
"""machines/production/model.ps1's own functions, run by pwsh (PowerShell 7) here; skipped where there is none.

Only what does not need Windows: the facts it reads, the line-up, the router's presets, the picker. The verbs
that touch the network, the firewall and the GPU are proved on bay 1."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPO / "machines" / "production" / "model.ps1"

# Loads every function from model.ps1 without running its verbs, then sets the few names they read.
PRELUDE = r'''
$ErrorActionPreference = 'Stop'
$path = '%(script)s'
$t = $null; $e = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$t, [ref]$e)
if ($e) { throw "model.ps1 does not parse: $($e[0].Message)" }
foreach ($f in $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $false)) {
    . ([scriptblock]::Create($f.Extent.Text))
}
$PSScriptRoot2 = Split-Path $path
$Facts = ReadFacts (Join-Path $PSScriptRoot2 'model.yml')
$Spread = Join-Path $PSScriptRoot2 'models'
$Root = '%(root)s'
$Up = Join-Path $Root 'up'
$Models = Join-Path $Root 'models'
$Preset = Join-Path $Root 'models.ini'
function Say($m) { Write-Output $m }
'''


@unittest.skipUnless(shutil.which("pwsh"), "no pwsh here")
class ModelPs1(unittest.TestCase):
    def run_ps(self, body):
        with tempfile.TemporaryDirectory() as root:
            (pathlib.Path(root) / "models").mkdir()
            self.root = pathlib.Path(root)
            test = self.root / "test.ps1"
            test.write_text(PRELUDE % {"script": SCRIPT, "root": root} + body, encoding="utf-8")
            r = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-File", str(test)],
                               capture_output=True, text=True, timeout=120, env=dict(os.environ, TERM="dumb"))
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            return r.stdout.splitlines()

    def test_nothing_is_up_until_something_is_picked(self):
        out = self.run_ps(r'''
"none: " + @(Chosen).Count
$kept = Choose @('gpt-oss-20b', 'nonesuch', 'qwen3.5-0.8b')
"kept: " + ($kept -join ',')
"read: " + ((Chosen) -join ',')
"answers: " + (Answerer @(Chosen) @{})
"loaded answers: " + (Answerer @(Chosen) @{ 'qwen3.5-0.8b' = 'loaded'; 'gpt-oss-20b' = 'unloaded' })
"nobody: " + ($null -eq (Answerer @() @{}))
Set-Content $Up "qwen3.8-27b`ngone-model"
"stale: " + ((Chosen) -join ',')
$null = Choose @()
"empty: " + @(Chosen).Count
''')
        self.assertEqual(out, ["none: 0",                               # never picked: nothing up, no default
                               "kept: gpt-oss-20b,qwen3.5-0.8b",
                               "read: gpt-oss-20b,qwen3.5-0.8b",
                               "answers: gpt-oss-20b",                  # the first that is up
                               "loaded answers: qwen3.5-0.8b",          # one already loaded: no swap on the card
                               "nobody: True",
                               "stale: qwen3.8-27b",
                               "empty: 0"])

    def test_the_router_serves_only_what_is_up_and_placed(self):
        out = self.run_ps(r'''
$null = Choose @('qwen3.5-0.8b', 'qwen3.5-9b')
foreach ($n in 'qwen3.5-4b', 'qwen3.5-0.8b') {          # placed: the right size; 9b is up but not here
    $m = Spec $n; $f = [IO.File]::Create((FileOf $m)); $f.SetLength([int64]$m['size']); $f.Close()
}
"served: " + ((WritePreset) -join ',')
''')
        self.assertEqual(out, ["served: qwen3.5-0.8b"])                # the 4B is placed but down

    def test_the_presets_pin_the_context_and_load_nothing_ahead(self):
        out = self.run_ps(r'''
PresetText @('qwen3.5-4b', 'gpt-oss-20b')
PresetText @('qwen3.5-0.8b', 'qwen3.8-27b')
''')
        models = str(self.root / "models")
        self.assertEqual(out, ["version = 1", "", "[*]", "c = 32768",
                               "", "[qwen3.5-4b]", "model = %s/Qwen3.5-4B-Q8_0.gguf" % models,
                               "", "[gpt-oss-20b]", "model = %s/gpt-oss-20b-MXFP4.gguf" % models, "",
                               "version = 1", "", "[*]", "c = 32768",
                               "", "[qwen3.5-0.8b]", "model = %s/Qwen3.5-0.8B-Q8_0.gguf" % models,
                               "", "[qwen3.8-27b]", "model = %s/Qwen3.8-27B-Q4_K_M.gguf" % models, ""])

    def test_the_picker_toggles_any_model_with_space(self):
        out = self.run_ps(r'''
$names = @(Names)
$keys = [System.Collections.Queue]::new()
function Keys($list) { $keys.Clear(); foreach ($k in $list) { $keys.Enqueue($k) } }
$read = { $keys.Dequeue() }
$quiet = { param($n, $s, $a) }
$four = [array]::IndexOf($names, 'qwen3.5-4b')
Keys (@('DownArrow') * $four + @('Spacebar', 'DownArrow', 'Spacebar', 'Enter'))     # the 4B down, the 9b up
"picked: " + ((PickLoop $names @('qwen3.5-4b') $read $quiet) -join ',')
Keys @('Spacebar', 'Escape')
"left: " + ($null -eq (PickLoop $names @('qwen3.5-4b') $read $quiet))
Keys @('UpArrow', 'Spacebar', 'Spacebar', 'Enter')                                  # on, then off again
"twice: " + ((PickLoop $names @('qwen3.5-4b', 'gpt-oss-20b') $read $quiet) -join ',')
''')
        self.assertEqual(out, ["picked: qwen3.5-9b", "left: True", "twice: gpt-oss-20b,qwen3.5-4b"])

    def test_a_model_that_always_reasons_reads_as_its_own_level(self):
        out = self.run_ps(r'''
$m = Spec 'gpt-oss-20b'
"$($m['thinking']) $($m['quick-effort']) $($m['considered-effort'])"
''')
        self.assertEqual(out, ["effort low medium"])


if __name__ == "__main__":
    unittest.main()
