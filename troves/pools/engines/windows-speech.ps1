<#
windows-speech.ps1 -- a pools transcription engine: Windows' dictation recognizer, nothing installed.
    windows-speech.ps1 -Wav FILE.wav     JSON on stdout: [{at, len, text, conf}, ...]
Rough on a room of people. Windows PowerShell 5.1, ASCII only. See troves/pools/README.md.
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
