#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
plist="$HOME/Library/LaunchAgents/com.moqalaqetabaza.local.plist"
mkdir -p "$HOME/Library/LaunchAgents" "$repo_dir/logs"

cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.moqalaqetabaza.local</string>
  <key>ProgramArguments</key>
  <array>
    <string>$repo_dir/scripts/start-local.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>$repo_dir</string>
  <key>StandardOutPath</key>
  <string>$repo_dir/logs/server.out.log</string>
  <key>StandardErrorPath</key>
  <string>$repo_dir/logs/server.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$plist" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$plist"
launchctl enable "gui/$(id -u)/com.moqalaqetabaza.local"

echo "Installed and started: com.moqalaqetabaza.local"
echo "Open http://127.0.0.1:8765/"
