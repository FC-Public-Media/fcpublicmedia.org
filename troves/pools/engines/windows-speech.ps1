<#
windows-speech.ps1 -- a transcription engine for the pools page, with nothing
installed: Windows' own desktop dictation recognizer (System.Speech, en-US).

    windows-speech.ps1 -Wav FILE.wav     JSON on stdout: [{at, len, text, conf}, ...]

ROUGH. It was made for one voice dictating into a headset, not a room of
people talking, and it shows. It is here to prove the transcription leg end to
end (a selection out, a transcript back on the timeline) until a real engine
is chosen and brought in the bay's way. `at` is seconds from the file's start,
by the recognizer's own running total. 16 kHz mono PCM suits it best.

Windows PowerShell 5.1, no modules. ASCII only.
#>
param([Parameter(Mandatory)] [string] $Wav)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine ([Globalization.CultureInfo]'en-US')
$r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$r.SetInputToWaveFile($Wav)
$r.BabbleTimeout = [TimeSpan]::FromSeconds(0)
$r.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.4)
$out = New-Object System.Collections.ArrayList
$at = 0.0
while ($true) {
    try { $res = $r.Recognize() } catch { break }
    if ($null -eq $res) { break }
    $len = $res.Audio.Duration.TotalSeconds
    [void]$out.Add([pscustomobject]@{ at = [math]::Round($at, 2); len = [math]::Round($len, 2); text = $res.Text; conf = [math]::Round($res.Confidence, 2) })
    $at += $len
}
$r.Dispose()
ConvertTo-Json -InputObject @($out) -Compress
