# 03 — Session State Machine

This section defines the CB session lifecycle: negotiation, register dump,
and steady-state operation.

## 3.1 Overview

```
  Ping    getSystemData   CAN2 in use     setCAN flush      getCAN dump      steady cycle
   │          │               │                │                 │               │
   ▼          ▼               ▼                ▼                 ▼               ▼
Init ──► Negotiate ──────► RequestDump ───► (two-phase) ──► Steady ──────► ping/ackCAN/setCAN/getCAN
```

The tablet maintains a register mirror (see `04-registers.md`) which is
populated by the dump and kept current by steady-state `getCAN` deltas.

## 3.2 Negotiation

1. CB begins transmitting `Ping` frames (~1 per second) on power-up.
2. The tablet replies to each `Ping` with `getSystemData` until the CB
   responds. The normal response on modern CBs is:
   - `CAN2 in use` — the CB announces its register (CAN2) protocol.
3. Negotiation is complete when the CB responds at all. The tablet should
   re-send `getSystemData` on every `Ping` until it does.

A `getSystemData` XML response during negotiation is a variant seen only on
CBs that implement the legacy command channel (`05-commands.md`); register-only
CBs always answer `CAN2 in use`.

## 3.3 Register dump (two-phase flush)

The tablet requests a full register dump with a two-phase flush:

**Phase 1 — dirty-reset flush (register 06, unit id `00000`):**

```
setCAN 0701000000600000000000000
```

This clears the CB's "dirty" flag so the subsequent flush returns the full
register set rather than only changed registers. Some CBs return nothing for
this phase — it is best-effort.

**Phase 2 — full flush:** the unit-scoped register-06 flush is then sent
(e.g. `setCAN 0801000000600000000000000 0801000000236000000000000` for an
RF-connected unit). The CB replies with a `getCAN` carrying all registers.

The CB may reply `getCAN 0` (nack) instead of the dump; the tablet must ack
and re-send the flush. The tablet must not re-send the dump on every `Ping`
while the CB is still delivering a large `getCAN` (overlapping transmit and
receive corrupts the burst).

On receipt of register `06` (JZ17, firmware status), the tablet:

- stores the firmware major/minor, CB type, and RF firmware major;
- replies with register `07` (JZ18) — all-zero payload, same unit type and
  unit id — acknowledging the firmware announcement. This reply is mandatory;
  a split-system CB may require it to be queued/paced rather than sent
  immediately.

## 3.4 Steady state

Each `Ping` grants the tablet one reply slot. Reply priority:

1. **`ackCAN`** — if a `getCAN` was received since the last `Ping`:
   `ackCAN 1` when the frame CRC was valid, `ackCAN 0` when it failed.
2. **`setCAN <records…>`** — queued register writes (from the control plane).
3. **Command / poll** — a queued legacy command string (see `05-commands.md`);
   register-only CBs ignore these.
4. **`getSystemData`** — while the system status register (05) is absent.
   Only answered by CBs with the legacy channel; on register-only CBs reg 05
   must be obtained from the dump / unit-scoped flush instead.
5. **`setCAN `** (empty) — register sync poll. Must be skipped while `CAN2
   in use` is outstanding.

The CB replies to each tablet frame with either:

- `getCAN <n> <records…>` — register state; `n = 0` means "re-send what you
  sent". Records are applied to the mirror; only changed registers are
  delivered in steady state.
- `CAN2 in use` — the CB is busy; the tablet must not send an empty `setCAN`
  while this is outstanding.
- an XML payload — the reply to a legacy command/poll, on CBs that implement
  the legacy channel (see `05-commands.md`).

Inbound register records are validated against the ranges in
`04-registers.md`; records outside range are rejected.

## 3.5 Register flush request (JZ16)

`0701000000600000000000000` is the canonical "flush all registers" request
(register 06, unit id `00000`, all-zero payload). It is the same message used
for the dirty-reset phase of the dump and is also sent at session start to
force a full register announcement.

## 3.6 Timing

| Parameter | Value | Notes |
|---|---|---|
| Ping interval | ~1 s | CB-driven |
| Register freshness window | 80 s | Reference-implementation guidance, not a CB requirement: a unit whose registers have not been seen for this long is considered stale |
| Split-system freshness window | 260 s | Ditto — RF-connected units |
| Zone-data freshness window | 160 s | Ditto — extended while zone data is being exchanged |
| Command retries | bounded | Implementations should bound resends (bus-level retry is via `getCAN 0` nacks and `ackCAN 0`) |

The freshness windows drive the tablet's "unit online/offline" determination:
a unit whose window expires is marked offline until its registers reappear.
They are tablet-side tuning values observed in reference implementations;
other values are valid.
