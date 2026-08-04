# 07 — Flows

## 7.1 Wireless sensor pairing

1. The user selects "pair with sensor"; the tablet prompts for the sensor's
   pair button to be pressed.
2. The user presses the pair button on the sensor. The sensor transmits a
   radio packet with the pairing bit set.
3. The CB radio detects the sensor and sends register `12` (JZ33) with the
   sensor UID and the pairing info byte (bit 6 set):

```
Ping / setCAN  / getCAN 1 0703abcde0a00000000000000 0703abcde1201613d400e0000
Ping / ackCAN 1
```

4. The tablet attaches the sensor to the zone the user selected by writing
   register `12` (JZ32):

```
Ping / setCAN 0701abcde1201613d01000000
```

   The payload is `[sensor UID 3 bytes][zone][000000]`.
5. The CB applies the attachment and thereafter populates the zone's
   measured temperature and sensor type in register `03` (JZ11) updates.

Notes:

- A zero sensor UID (`000000`) is rejected by the tablet on inbound pairing
  notifications.
- The tablet may pair the sensor by zone without a UID when the pairing flow
  is driven from the zone side; the CB then fills in the UID.
- RF devices can additionally be registered and calibrated with registers
  `26` (JZ55) and `27` (JZ57) — see `04-registers.md`.

## 7.2 Activation code

The installer sets an activation code via `setActivation?json=…` or writes
register `09` (JZ23):

```
[07|08][01][00000][09][action][codeHi][codeLo][days][000000]
```

- `action` 1 = set new code, 2 = unlock.
- `codeHi`/`codeLo` are the two bytes of the unlock code.
- `days` is the activation period in days; the system locks when it expires
  (activation status becomes 2 = expired, register `02`).
- Register `02` byte 1 reports the resulting status.

## 7.3 System start / register dump

1. CB pings; tablet negotiates (§3.2).
2. Tablet sends the global flush `0701000000600000000000000` (register 06,
   unit id `00000`), then the unit-scoped flush; CB answers with the full
   register set (§3.3).
3. On each register `06` (JZ17) announcement, the tablet answers register
   `07` (JZ18) all-zero.
4. Steady state begins: register deltas are delivered as `getCAN` on every
   change (§3.4).
5. The tablet re-requests a full dump at any time by re-sending the flush.

## 7.4 Multi-unit systems

- A CB may be one of several: the unit id (`UUUUU`) distinguishes units, and
  multiple CBs can be chained on the bus.
- Systems configured for a single unit reject a second unit's register
  traffic (`07`/`08` unit types) and flag "multiple units detected".
- Split-type systems (cbType 4/5) appear as unit type `08`; their register
  writes must echo unit type `08`.

## 7.5 Unit freshness

A unit is considered online while its register traffic is being received.
Freshness windows (see `03-session.md §3.6`):

| Unit kind | Window |
|---|---|
| Wired (type 07) | 80 s |
| Split system (type 08) | 260 s |
| Zone-data exchange | 160 s |

When the window expires the unit is marked offline until traffic resumes.

## 7.6 Error handling

- `getCAN 0` nacks: the tablet acks (`ackCAN 1`) and re-sends the previous
  `setCAN`.
- Failed CRC: the tablet replies `ackCAN 0`; the CB retransmits.
- `CAN2 in use`: the CB is busy; the tablet withholds empty `setCAN` frames
  and retries its poll on the next ping.
- Register values outside the documented ranges are rejected and logged.
