param(
  [string]$TaskName = "ThreatFeedFetch",
  [int]$IntervalMinutes = 60,
  [string]$Python = "python",
  [string]$WorkingDir = (Resolve-Path ".").Path,
  [string]$Feeds = "config/feeds.json",
  [string]$Db = "data/iocs.db",
  [string]$ExportJson = ""
)

$fetchArgs = "run_cli.py fetch --feeds $Feeds --db $Db"
if ($ExportJson -ne "") {
  $fetchArgs = "$fetchArgs --export-json $ExportJson"
}

$command = "cmd /c cd /d `"$WorkingDir`" && $Python $fetchArgs"

schtasks /Create /F /SC MINUTE /MO $IntervalMinutes /TN $TaskName /TR $command
