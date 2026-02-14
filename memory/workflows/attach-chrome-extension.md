# Attach Chrome Extension Relay

## Method: Peekaboo pixel click

The OpenClaw 🦞 extension icon is at fixed position **(1718, 93)** in Chrome's toolbar.

```bash
# 1. Make sure Chrome is frontmost
peekaboo click --app "Google Chrome" --at 1718,93
```

## Notes
- Element ID changes between screenshots but position is stable
- Confirmed by Ops agent (2026-02-14)
- If Chrome window is resized/moved, position may shift — re-check with `peekaboo see --app "Google Chrome" --annotate`
- After clicking, verify with: `browser action:tabs profile:chrome`
