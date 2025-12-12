#!/usr/bin/env bash
set -euo pipefail

# Streamlit Community Cloud build hook.
# Goal: ensure a Chrome/Chromium binary exists for Plotly/Kaleido static image export.

echo "[postBuild] whoami: $(whoami)"
echo "[postBuild] pwd: $(pwd)"
echo "[postBuild] python: $(command -v python || true)"
echo "[postBuild] python3: $(command -v python3 || true)"
echo "[postBuild] pip: $(command -v pip || true)"
echo "[postBuild] pip3: $(command -v pip3 || true)"

# Some Streamlit build images may already have chrome from packages.txt; surface it.
echo "[postBuild] chrome: $(command -v google-chrome || true)"
echo "[postBuild] chromium: $(command -v chromium || true)"
echo "[postBuild] chromium-browser: $(command -v chromium-browser || true)"

# If Plotly's helper is present, try it (no-op if already installed).
if command -v plotly_get_chrome >/dev/null 2>&1; then
  echo "[postBuild] running plotly_get_chrome"
  plotly_get_chrome || true
else
  echo "[postBuild] plotly_get_chrome not found on PATH"
fi

# Final state
echo "[postBuild] chrome after: $(command -v google-chrome || true)"
