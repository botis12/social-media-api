#!/usr/bin/env bash
# ============================================================
#  APEX PERFORMANCE — local preview launcher (Mac / Linux)
#  Double-click this file. It starts a local web server in this
#  folder and opens the site in your browser.
#  To stop it: press Ctrl+C, or just close the window.
# ============================================================
cd "$(dirname "$0")" || exit 1

if [ ! -f index.html ]; then
  echo "ERROR: index.html is not in this folder."
  echo "Move this launcher into the 'website' folder and try again."
  read -r -p "Press Enter to close."
  exit 1
fi

# Find a free port starting at 8080
PORT=8080
while lsof -i :$PORT >/dev/null 2>&1 || nc -z 127.0.0.1 $PORT >/dev/null 2>&1; do
  PORT=$((PORT + 1))
  [ $PORT -gt 8100 ] && { echo "No free port found."; read -r -p "Press Enter to close."; exit 1; }
done

URL="http://localhost:$PORT"
echo "------------------------------------------------------------"
echo "  Serving this folder at:  $URL"
echo "  Keep this window OPEN. Press Ctrl+C to stop."
echo "------------------------------------------------------------"

# Open the browser shortly after the server comes up
( sleep 1.5; (command -v open >/dev/null && open "$URL") || (command -v xdg-open >/dev/null && xdg-open "$URL") ) >/dev/null 2>&1 &

# Use whichever runtime is installed
if   command -v python3 >/dev/null 2>&1; then exec python3 -m http.server "$PORT"
elif command -v python  >/dev/null 2>&1; then exec python  -m http.server "$PORT"
elif command -v php     >/dev/null 2>&1; then exec php -S "localhost:$PORT"
elif command -v npx     >/dev/null 2>&1; then exec npx --yes http-server -p "$PORT" .
else
  echo "Could not find Python, PHP or Node on this computer."
  echo "Install Python from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close."
fi
