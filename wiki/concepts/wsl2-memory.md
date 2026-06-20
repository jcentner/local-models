---
title: WSL2 memory cap
tags: [concept, wsl2, environment]
updated: 2026-06-14
status: verified
---

# WSL2 memory cap (why WSL only sees ~half your RAM)

A practical gotcha that directly limits which models fit on any WSL2 box.

## The rule

**By default WSL2 caps guest memory at roughly 50% of host RAM** (or 8 GB,
whichever is higher), unless a `.wslconfig` overrides it. So a model that fits the
machine's physical RAM can still fail to load inside WSL.

## Example (this dev box)

32 GB of host RAM, but inside WSL2:

```
$ free -h
               total        used        free      ...
Mem:            15Gi       7.0Gi       5.8Gi      ...
```

WSL2 only exposes **~15 GB** — the 50% default, no `.wslconfig` present.

## Why it matters

Total available memory must exceed the quantized model size. Examples:

- **DiffusionGemma** Q4_K_M needs **~18 GB** total -> **does not fit** in the
  default 15 GB. See [models/diffusiongemma.md](../models/diffusiongemma.md).
- Any 13B+ model relying on CPU offload is constrained by this cap, not by the
  32 GB on the box.

## The fix

Create `C:\Users\<YourWindowsUser>\.wslconfig` (on the **Windows** side) from
[env/wslconfig.template](../../env/wslconfig.template):

```ini
[wsl2]
memory=24GB
processors=20
swap=8GB
```

Then, from a Windows terminal:

```powershell
wsl --shutdown
```

Reopen Ubuntu and confirm with `free -h` (should show ~24Gi).

> [!WARNING]
> `wsl --shutdown` closes **all** WSL sessions, including the VS Code one. Save
> first. Leave Windows ~8 GB headroom (don't set `memory` to the full 32 GB).

## Verify

`bash scripts/verify-stack.sh` prints the WSL-visible RAM and warns when it's
below the ~18 GB threshold that bigger models want.

## Related
- [hardware/proart-p16.md](../hardware/proart-p16.md)
- [models/diffusiongemma.md](../models/diffusiongemma.md)
