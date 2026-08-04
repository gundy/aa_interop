# 05 — Legacy Command Channel (XML)

> **Status: legacy / alternate channel — not universally supported.**
>
> The register channel (`04-registers.md`) is the **normative and complete**
> control surface: every functional operation — power, mode, fan, temperature,
> zones, sensors, pairing, errors — is available through register records and
> requires no command channel at all.
>
> The command channel described here is a legacy request/response mechanism
> that **some** Control Boxes implement and others do not. A CB that does not
> support it simply does not answer (or ignores) command strings; every
> function still works through registers. Implementations MUST NOT require the
> command channel for any functionality, and MUST treat it as best-effort:
> send a command, and accept that no reply (or no effect) may follow.

Commands are plain ASCII strings transmitted in the tablet's reply slot
(priority 3 in `03-session.md §3.4`). On CBs that support it, the CB replies
with an XML payload in a subsequent frame; the tablet matches replies by the
`<request>` tag content. Commands are only useful for legacy actions and data
that has no register representation (zone names, installer settings, schedule
programming).

## 5.1 Command catalog

All commands below are legacy: a CB that does not support the command channel
ignores them. Register equivalents exist for every functional command (see
`04-registers.md`); the XML reply schemas in §5.2–5.4 apply only to CBs that
implement the channel.

### Polls (request data)

| Command | Reply |
|---|---|
| `getSystemData` | full system XML (§5.2) |
| `getZoneData?zone=N` | zone XML (§5.3); `N` = 1–10 |
| `getClock` | clock XML (minimal, unverified fields) |
| `getZoneTimer` | zone timer data (schedule XML, §5.4) |
| `getScheduleData?schedule=N` | schedule XML (§5.4); `N` = 1–5 |

### Commands (set state)

| Command | Effect |
|---|---|
| `setSystemData?mode=N` | Set system mode; `N` per `06-enums.md` (1–6) |
| `setSystemData?airconOnOff=1` | Turn the system on |
| `setSystemData?logoPIN=0000` | Set the installer logo PIN |
| `setSystemData?dealerPhoneNumber=0000000000` | Set the dealer phone number |
| `setZoneData?zone=N&zoneSetting=0\|1` | Close/open zone `N` |
| `setZoneData?zone=N&name=…` | Rename zone `N` |
| `setAircon?json={…}` | Bulk JSON update (aircon + zones); see §5.5 |
| `setActivation?json={…}` | Set activation code (JSON: `activationCode`, `setActivationCode`, `setActivationTime`, `unlockCode`) |
| `setZoneTimer?startTimeHours=H&startTimeMinutes=M&endTimeHours=H&endTimeMinutes=M&scheduleStatus=S` | Set the zone timer |
| `setScheduleData?schedule=N&day=&startHours=H&startMinutes=M&endHours=H&endMinutes=M&scheduleStatus=S&zoneStatus=Z&zones=…` | Set schedule `N`; `zones` is one `0/1` digit per zone |

Command replies echo the affected state as XML (e.g. `setSystemData?mode=1`
is answered with the system XML, `setZoneData` with the zone XML).

## 5.2 `getSystemData` reply schema

The reply is an XML document. The `<request>` tag identifies the query.

> **Two dialects exist in the wild.** Reference implementations parse
> `getSystemData` replies in two different shapes: a flat-tag dialect
> (Dialect A below) and a nested `<aircon><info>` dialect (Dialect B). The two
> are documented from different implementation lineages; it is not known
> whether a given CB emits one, the other, or a superset containing both.
> **None of these schemas has been observed on a live bus** — treat them as
> reference material for the legacy channel, not verified wire truth.

### Dialect A — flat tags

Characteristic tags:

| Tag | Type | Meaning |
|---|---|---|
| `iZS10.3` | marker | Version-marker element; must be present |
| `request` | string | `getSystemData` |
| `mac` | string | CB MAC address |
| `mid` | string | CB unit id (matches register `0a`) |
| `name` | string | System name |
| `CBrev` | string | CB firmware, `major.minor` |
| `zoneStationHasUnitControl` | int | Unit type |
| `airconOnOff` | int | 0/1 system state |
| `fanSpeed` | int | 0 = off, 1 = low, 2 = medium, 3 = high, 4 = auto |
| `mode` | int | 1 = cool, 2 = heat, 3 = vent, 4 = auto, 5 = dry |
| `ACinfo` | int | Unit-control info |
| `unitControlTempsSetting` | int | MyZone id (0 = disabled) |
| `centralDesiredTemp` | float | Set temperature °C |
| `airConErrorCode` | string | Error code (see register 08) |
| `activationCodeStatus` | int | 0 = none, 1 = enabled, 2 = expired |
| `numberOfZones` | int | |
| `numberofConstantZones` | int | |
| `zsConstantZone1` | int | Constant zone 1 (0 = disabled) |
| `zsConstantZone2` | int | |
| `zsConstantZone3` | int | |
| `logoPIN` | string | Installer PIN |
| `dealerPhoneNumber` | string | |
| `systemID` | int | RF system id |
| `tempSensorNotConfigured` | bool | |
| `FAstatus` | int | 0 = none, 1 = off, 2 = on |
| `cbType` | int | CB type (see `06-enums.md`) |

### Dialect B — nested `<aircon><info>`

Characteristic tags:

| Tag | Type | Meaning |
|---|---|---|
| `request` | string | `getSystemData` |
| `aircon > info > state` | string | `on` / `off` |
| `aircon > info > mode` | string | `cool`/`heat`/`vent`/`auto`/`dry`/`myauto` |
| `aircon > info > fan` | string | `off`/`low`/`medium`/`high`/`auto`/`auto_aa` |
| `aircon > info > setTemp` | float | Set temperature °C |
| `aircon > info > myZone` | int | MyZone id (0 = disabled) |
| `aircon > info > freshAir` | string | `on` / `off` / `none` |

The tablet additionally patches transport-specific tags in this dialect:
`type`, `AppStore`, `dhcp`, `subnet`, `gateway`, `MyAppRev` are tablet/install
context fields substituted by the tablet before the document is consumed
downstream; they are not meaningful CB state.

## 5.3 `getZoneData?zone=N` reply schema

| Tag | Type | Meaning |
|---|---|---|
| `request` | string | `getZoneData` |
| `zone` | int | Zone number |
| `name` | string | Zone name (URL-decoded) |
| `setting` | int | 0 = closed, 1 = open |
| `userPercentSetting` | int | Damper percent |
| `minDamper` | int | |
| `maxDamper` | int | |
| `desiredTemp` | float | Set temperature °C |
| `actualTemp` | float | Measured temperature °C |
| `RFstrength` | int | RSSI |
| `hasLowBatt` | bool | Low battery → zone error bit 1 |
| `tempSensorClash` | bool | Sensor clash → zone error bit 0 |
| `motionCurrentState` | int | Motion status |
| `hasClimateControl` | bool | 1 = climate-control sensor (zone type 1), 0 = percent zone |

## 5.4 Schedule / timer XML

`getScheduleData?schedule=N` replies contain at minimum a `schedule` element
(the schedule number) and the schedule state fields used by
`setScheduleData` (`startHours`, `startMinutes`, `endHours`, `endMinutes`,
`scheduleStatus`, `zoneStatus`, `zones`). The `zones` value is one `0/1`
character per zone.

`getZoneTimer` replies carry the zone timer state with the same fields as
`setZoneTimer` (`startTimeHours`, `startTimeMinutes`, `endTimeHours`,
`endTimeMinutes`, `scheduleStatus`).

## 5.5 `setAircon` JSON

The JSON body is a subset of the tablet API document structure (see
`../../tablet_api/README.md`):

```json
{"aircons": { "ac1": { "info": { "state": "on", "mode": "cool" } } } }
{"aircons": { "ac1": { "zones": { "z02": { "state": "open" } } } } }
```

Field semantics:

| Info field | Values | Maps to |
|---|---|---|
| `state` | `on` / `off` | register 05 byte 0 |
| `mode` | `cool`/`heat`/`vent`/`auto`/`dry`/`myauto` | register 05 byte 1 |
| `fan` | `off`/`low`/`medium`/`high`/`auto`/`auto_aa` | register 05 byte 2 |
| `setTemp` | float °C | register 05 byte 3 (× 2) |
| `myZone` | int | register 05 byte 4 |
| `freshAir` | `on` / `off` | register 05 byte 5 |

| Zone field | Values | Maps to |
|---|---|---|
| `state` | `open` / `close` | register 03 byte 1 bit 7 |
| `value` | 0–100 | register 03 byte 1 bits 6–0 |
| `setTemp` | float °C | register 03 byte 3 (× 2) |

Sparse payloads are merged over the current register state — absent fields
are left untouched.

## 5.6 Blocked commands

Commands whose name contains `Light`, `Aircon` (other than `setAircon`),
`Activation` or `MySystem` are not placed on the bus by the reference
transport. `setAircon` is handled through the register path (§5.5), not as a
raw command string.
