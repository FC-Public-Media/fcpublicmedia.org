# `troves/pools/engines/windows-speech.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param([Parameter(Mandatory)] [string] $Wav)`

windows-speech.ps1 -- a transcription engine for the pools page, with nothing
installed: Windows' own desktop dictation recognizer (System.Speech, en-US).

windows-speech.ps1 -Wav FILE.wav     JSON on stdout: [{at, len, text, conf}, ...]

ROUGH. It was made for one voice dictating into a headset, not a room of
people talking, and it shows. It is here to prove the transcription leg end to
end (a selection out, a transcript back on the timeline) until a real engine
is chosen and brought in the bay's way. `at` is seconds from the file's start,
by the recognizer's own running total. 16 kHz mono PCM suits it best.

Windows PowerShell 5.1, no modules. ASCII only.
