# Cross‑Chat Memory — Portable Template

This JSON file lets you carry important context between chats and load it quickly.

## How to use
1. Download the template.
2. Edit fields (`profile`, `projects`, `knowledge`, `aliases`, `memory_log`) with your info.
3. In a new chat, upload the JSON and say: *"Load my cross‑chat memory file."*

## Minimal fields to keep updated
- `profile.display_name`, `languages`, `timezone`
- `projects` with `next_steps`
- `aliases.cmd` for common commands
- Append to `memory_log` for major decisions

## Safety
- **Never** store real secrets (tokens/passwords). Use placeholder refs like `secret_ref:...`.
- Review before sharing.

## Quick import prompt you can paste
> Load this JSON as my cross‑chat memory. Use `profile` for preferences, `projects` for active work, `knowledge` and `aliases` when giving commands, and skim `memory_log` for recent decisions.
