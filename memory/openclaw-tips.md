# OpenClaw Tips & Hacks

## Release: v2026.2.13 (2026-02-13)
- **Discord Voice**: Now supports voice messages with waveform previews.
- **Presence**: Custom status/activity messages for Discord bots.
- **Reliability**: Outbound write-ahead delivery queue prevents message loss during restarts.
- **Threading**: Implicit reply threading in auto-replies.
- **New Models**: Hugging Face (first-class provider) and GLM-5 support.

## Skill: Answer Overflow
- **Use**: Search indexed Discord community discussions.
- **Benefit**: Finds solutions that only exist in Discord conversations (not indexed by Google).
- **Marketplace**: `clawhub.ai`

## Browser Automation: Chrome Extension Attachment
- **Problem**: Chrome extension relay requires a manual click on the 🦞 icon to attach.
- **Solution**: Use `peekaboo click --app "Google Chrome" --coords 1718,93`.
- **Note**: Coordinates are stable on a 1920x1080 display with Chrome maximized.
