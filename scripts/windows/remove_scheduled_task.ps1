param(
  [string]$TaskName = "ThreatFeedFetch"
)

schtasks /Delete /F /TN $TaskName
