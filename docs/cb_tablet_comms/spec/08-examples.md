# 08 — Examples

Annotated wire captures. `Ping` frames are elided where they only grant the
tablet its reply slot.

## 8.1 Negotiation and register dump

```
<U>Ping</U=db>
<U>getSystemData</U=15>
<U>Ping</U=db>
<U>CAN2 in use</U=…>          ← CB announces bus busy; tablet keeps polling
<U>Ping</U=db>
<U>getSystemData</U=15>
…
<U>Ping</U=db>
<U>getSystemData</U=15>
<U>Ping</U=db>
<U>CAN2 in use</U=…>
<U>Ping</U=db>
<U>setCAN 0701000000600000000000000</U=…>   ← JZ16 global flush (dirty reset)
<U>getCAN 1 0703abcde0600000000000000</U=…>  ← CB announces itself (reg 06)
<U>Ping</U=db>
<U>ackCAN 1</U=aa>
<U>Ping</U=db>
<U>setCAN 0801000000600000000000000 0801000000236000000000000</U=…>  ← unit-scoped flush
```

## 8.2 Initial register status dump

The CB replies to the flush with its full register set:

```
getCAN 1 0703abcde0a00000000000000 0703abcde1201613d400e0000 0703abcde0501010330000100
         0703abcde0841413400000000 0703abcde1300000000000000 0703abcde0301e40030000000
         0703abcde0401006400010000 0703abcde0302640030000000 0703abcde0402146400010000
         0703abcde0303e40030000000 0703abcde0403006400010000 0703abcde0304640030000000
         0703abcde0404006400010000 0703abcde0305640030000000 0703abcde0405006400010000
         0703abcde0306640030000000 0703abcde0406006400010000 0703abcde0307640030000000
         0703abcde0407006400010000 0703abcde0308640030000000 0703abcde0408006400010000
         0703abcde0309640030000000 0703abcde0409006400010000 0703abcde030a640030000000
         0703abcde040a006400010000 0703abcde0211001116000000
```

Decode of selected records (unit `abcde`):

| Record | Decode |
|---|---|
| `0a00000000000000` | JZ24 unit announcement (reg 0a) |
| `1201613d400e0000` | JZ33 pairing notification: sensor UID `01613d`, info `40` (pair bit), rev `0e` |
| `0501010330000100` | JZ15 system status: on, cool, high, 24 °C (0x30/2), no myzone, fresh air on, RF id 0 |
| `0841413400000000` | JZ22 error: `AA14` |
| `13 00000000000000` | JZ35 info byte 0 |
| `0301e40030000000` | JZ11 zone 1: open (0xe4 = 0x80|0x64), sensor 0, set 24 °C, no measured temp |
| `0401006400010000` | JZ13 zone 1: min 0, max 100, motion 0, config 1, error 0, RSSI 0 |
| `0211001116000000` | reg 02: unit type `11` (Daikin), activation `00`, FW `11 16` |

## 8.3 Sensor pairing flow

```
Ping / setCAN  / getCAN 1 0703abcde0a00000000000000 0703abcde1201613d400e0000   ← sensor detected (pair bit set)
Ping / ackCAN 1
Ping / setCAN 0701abcde1201613d01000000                                        ← attach sensor 01613d to zone 1
```

After attachment the CB populates zone 1's measured temperature in
subsequent `getCAN` register-03 records.

## 8.4 Steady state — zone update

```
Ping / setCAN 0701abcde0301e40030000000    ← tablet writes zone 1 open/100%, set 24 °C
getCAN 1 0703abcde0301e40130000000         ← CB confirms: zone 1 open/100%, RF sensor (01), no temp yet
Ping / ackCAN 1
Ping / setCAN 
getCAN 1 0703abcde0301e40114090a0000       ← sensor attached: measured temp 20.5 °C now populated
Ping / ackCAN 1
```

After a sensor is attached (register 12), the CB populates the sensor-type
byte and measured temperature in subsequent register-03 records.

## 8.5 Legacy command channel (only on CBs that support it)

```
Ping / setSystemData?mode=1        ← legacy command: set mode to cool
… / <request>getSystemData</request><iZS10.3>…</iZS10.3>…   ← reply, if the CB implements the legacy channel
```

Register-only CBs ignore the command; the equivalent operation is the
register-05 write shown in §8.4.

## 8.6 RF device registration

```
Ping / setCAN 0701abcde2601000000000000     ← JZ55: RF device type 01 (type 07), zone channel 00
Ping / setCAN 0801abcde2701000000000000     ← JZ57: calibration control 01, channel 00, position 00
```

(Byte values illustrative; see `04-registers.md` for field placement.)
