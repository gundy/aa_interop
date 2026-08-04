# Tablet to Control Box connection

The connection between the Tablet and Control box uses an ethernet cable.

The cable carries both power and data to the Tablet.

## Physical Connector

The RJ45 connection between the Control Box and the tablet has the following pinout:

| Pin | T568A colour | T568B colour |  Description |
| --- | ------------ | ------------ | ------------ |
| 1   | green/white | orange/white | RS485 Comms (B)+ |
| 2   | green | orange | RS485 Comms (A)- |
| 3   | orange/white | green/white | unused |
| 4   | blue | blue | GND |
| 5   | blue/white | blue/white | ~14V DC power to tablet |  
| 6   | orange | green | GND |
| 7   | brown/white | brown/white | unused |
| 8   | brown | brown | unused |
| Shield | | | GND |

## Serial Port Settings

The communications between the CB and the Tablet uses half-duplex differential RS485 serial.

The communications settings used are: `57600bps`, `8N1`.

In order to communicate with the Control Box, or listen in to communications between the Control Box and Tablet, you will need an RS485 adaptor.  RS485 to USB adaptors can be found cheaply on ebay and other similar sites.

To help study the communications, I fashioned a cable using three RJ45 keystone sockets, all wired in parallel.  

The Control Box and Tablet were connected to two of the ports, and to the third I connected an ethernet cable with one end cut off, and the Green/Green+White wires connected to A & B of my RS485 adapter respectively, and the solid blue wire to ground.  

_My cable was wired using the T568A standard. Please be careful when wiring your own cables if you're blindly following the colour codes._

# Communications Protocol Overview

> **Normative specification:** the documents under [`spec/`](spec/) are the
> normative reference for the protocol. This file provides the overview and
> community notes.

| Document | Contents |
| --- | --- |
| [spec/01-physical.md](spec/01-physical.md) | Physical layer, bus ownership |
| [spec/02-framing.md](spec/02-framing.md) | Frame envelope, CRC-8, record format, unit types |
| [spec/03-session.md](spec/03-session.md) | Session state machine, dump, steady state, timing |
| [spec/04-registers.md](spec/04-registers.md) | Register catalog (byte-exact) |
| [spec/05-commands.md](spec/05-commands.md) | Legacy command channel (conditional): commands + XML reply schemas |
| [spec/06-enums.md](spec/06-enums.md) | Data dictionary (enums, error codes) |
| [spec/07-flows.md](spec/07-flows.md) | Sensor pairing, activation, multi-unit flows |
| [spec/08-examples.md](spec/08-examples.md) | Annotated wire captures |

## Ping messages

When powered up, the Control Box (almost) immediately begins sending `Ping` messages to the serial port.  

Each `Ping` message is followed by approximately one second of dead-time (during which the Tablet can communicate, more on that below).

The messages are wrapped in a curious form of XML. An example of what a Ping message looks like is given below:

> `<U>Ping</U=db>`

Each message from the Control Box is separated from the previous with a `SPACE` (`0x20`) character.

If you connect into a Control Box without any Tablet connected 
you get an endless sequence of these `Ping` messages (with the dead-time between messages as mentioned above):

> `<U>Ping</U=db> ... 1 second ... <U>Ping</U=db>  ... 1 second ... <U>Ping</U=db>  ... 1 second ... <U>Ping</U=db> ...`


## CRC

The `=db` inside the XML close element tag is a hexadecimal CRC8 check code that is used to validate the content of the enclosed message.

For the `Ping` messages shown above, the CRC value is `db` because `CRC8("Ping") == 0xdb`.

### Calculating CRC Checksums

The algorithm used is CRC8.

The parameters used for the CRC8 calculation are:

> Initial value: `0x00`

> Polynomial: `0xb2`   (x^8 + x^7 + x^5 + x^4 + x)

> Final XOR: `0xff`

In order to determine these parameters, I took some of the messages that I captured,
and wrote a small program to scan through the different possible polynomial values. 
Please refer to the code in `findpolynomial.c` for more information on how that worked.

### C code to calculate the CRC8 check code:

```c
uint8_t CRC8(const uint8_t *data, int length) 
{
   uint8_t crc = 0x00;

   for(int i=0; i<length; i++)
   {
      crc ^= *data++; 
      for (int j=0; j<8; j++) {
          if ((crc & 0x01) > 0) {
              crc = (crc >> 1) ^ 0xB2;
          } else {
              crc >>= 1;
          }
      }
   }
   return crc ^ 0xff;
}
```

## Two channels: registers (normative) and legacy commands

The protocol carries two kinds of traffic:

- **Registers** — a synchronised set of state registers mirrored between the
  CB and the tablet (`setCAN`/`getCAN`/`ackCAN`). Register payloads are
  fixed-width hex records; the CB pushes changed registers automatically.
  **This is the normative and complete control surface**: power, mode, fan,
  temperature, zones, sensors, pairing and errors are all carried by
  registers, and a CB can be fully operated with register traffic alone.
- **Commands (legacy)** — one-shot request/response strings
  (e.g. `setSystemData?mode=1`, `getZoneData?zone=3`) answered with XML
  payloads, where supported. **Not all CBs implement this channel**; modern
  CBs answer `CAN2 in use` to `getSystemData` and ignore command strings, and
  every function still works through registers. Commands are only useful for
  legacy actions and data with no register representation (zone names,
  installer settings, schedule programming), on CBs that support them.

See [spec/03-session.md](spec/03-session.md) and
[spec/05-commands.md](spec/05-commands.md).

# Control Box Operation

The Control Box is the only station that transmits unsolicited traffic: it
sends `Ping` messages, and it sends `getCAN` register updates whenever a
register changes (a temperature reading, a damper position, an error
condition).

# Basic Packet Structure

A register record is a 25-character hex string:

> `0701abcde1201234501000000`

| Fragment | Meaning |
| --- | --- |
| `07` | Unit type (`07` aircon, `08` RF-connected aircon / RF device, `02` lights) |
| `01` | Destination (`01` = Control Box, `03` = Tablet) |
| `abcde` | 20-bit unit id (unique identifier of the CB to address) |
| `12` | Register id |
| `01234501000000` | 7 bytes of register data |

See [spec/02-framing.md](spec/02-framing.md) for the full framing rules.

# Division of responsibility between Control Box and Tablet

## Control Box

The Control Box is responsible for:

- interacting with the attached HVAC system
- keeping track of and controlling zone motors
- interacting with attached zone temperature sensors
- listening for and decoding radio messages from temperature sensors
- controlling the "myzone" functionality

## Tablet

The Tablet is responsible for:

- interacting with the user; providing a nice facade on top of low-level CB messages.
- managing schedules and scenes (updating HVAC state based on time or other external stimulus like weather)
- implementing myauto/mytemp features (these are tablet-side: the CB never
  transmits a "myauto" mode; the tablet presents it and synthesises the
  corresponding register writes)
- managing zone grouping/following (zones that follow another zone's state)
- keeping track of ID's of temperature sensors that have been attached to zones.
- exposing an API that the phone app can communicate with
- exposing TeamViewer remote endpoint for support staff

# Message flow

As mentioned above, the RS-485 communications between the Tablet and CB is half-duplex, so if both the Control Box and Tablet were trying to send data at the same time, packets would get corrupted.

To work around this, the Control Box sends regular `Ping` messages followed by dead-time of approximately one second, during which the Tablet is allowed to send messages. 

Bus arbitration depends on this sequence of events.

Note: After the tablet has sent a message to the Control Box, the Control Box responds (almost) immediately with another Ping, so message flow is not limited by the one-second dead-time described above.  In practice dozens of messages are sent backwards and forwards every second.

## Initialisation / Protocol Negotiation

The first message that the Tablet sends to the Control Box is:

> `<U>getSystemData</U=15>`

.. to which the Control Box (at least this is the case for the CB9) responds:

> `<U>CAN2 in use</U=95>`

The current working assumption is that this is some sort of protocol negotiation, where the Control Box is telling the tablet to use "CAN2" format messages. I do not know what other responses might be possible here as I only have a CB9 box to study.  

## CAN(2) protocol

The CAN(2) protocol provides a simple way of synchronising data between the control box and the tablet.

## Writing values to the Control Box registers

Register writes are performed using `setCAN` messages.

`setCAN` messages are sent _from_ Tablet _to_ CB.

The structure of a `setCAN` message is:

`setCAN (<register definition>)*`

`setCAN` messages can write zero or more registers at a time.


## Reading values from the Control Box registers

In order to read data from the Control Box, the tablet must first send a `setCAN` message.  The very first `setCAN` message sent should be `setCAN 0701000000600000000000000` which seems to be a trigger for the CB send the content of all registers.

The response to a `setCAN` message is a `getCAN` message from the Control Box.  The `getCAN` message contains updates for zero or more registers.

The control box keeps track of what values it has previously sent to the tablet, so only registers that have changed are sent in each new update.

Finally, the Tablet sends an `ackCAN` message back to the Control Box to acknowledge receipt of the `getCAN` message.  

## Putting it all together: Standard flow

### Protocol Negotiation

| Message Direction | Message | Description |
| ----------------- | ------- | ----------- |
| CB -> Tablet | `<U>Ping</U=db>` | Ping Message |
| Tablet -> CB | `<U>getSystemData</U=15>` | Protocol Negotiation |
| CB -> Tablet | `<U>CAN2 in use</U=95>` | CAN2 protocol selected |

At this point the Tablet knows that it needs to use the CAN2 protocol to communicate with the CB.

### Reset Message and initial flows

| Message Direction | Message | Description |
| ----------------- | ------- | ----------- |
| CB -> Tablet | `<U>Ping</U=db>` | Ping from CB signals next available slot for Tablet |
| Tablet -> CB | `<U>setCAN 0701000000600000000000000 </U=5a>` | Tablet asks to reset CB "dirty" flag so CB will send all data | 
| CB -> Tablet | `<U>getCAN 1 0703abcde0a00000000000000 0703abcde0120030101000000 0703abcde0501010330000100 0703abcde0841413400000000 0703abcde1300000000000000 0703abcde0301e40030000000 0703abcde0401006400010000 0703abcde0302640030000000 0703abcde0402146400010000 0703abcde0303e40030000000 0703abcde0403006400010000 0703abcde0305640030000000 0703abcde0405006400010000 0703abcde0306640030000000 0703abcde0406006400010000 0703abcde0307640030000000 0703abcde0407006400010000 0703abcde0308640030000000 0703abcde0408006400010000 0703abcde0309640030000000 0703abcde0409006400010000 0703abcde030a640030000000 0703abcde040a006400010000 0703abcde0211001116000000 </U=d8>` | Initial register status dump |
| CB -> Tablet | `<U>Ping</U=db>` | Ping from CB signals next available slot for Tablet |
| Tablet -> CB | `<U>ackCAN 1</U=aa>` | Tablet acknowledges successful receipt of previous message from CB |

At this point the Tablet has a full dump of the Air Conditioning related registers from the Control Box, knows which AC units exist, and the Tablet will now enter a polling loop.

| Message Direction | Message | Description |
| ----------------- | ------- | ----------- |
| CB -> Tablet | `<U>Ping</U=db>` | Ping from CB signals next available slot for Tablet |
| Tablet -> CB | `<U>setCAN </U=b2>` | Tablet tells CB it has no updates for any registers |
| CB -> Tablet | `<U>getCAN 1 0703xxxxxYYzzzzzzzzzzzzzz</U=zz>` | CB responds with any registers that it has changed since the last poll |
| CB -> Tablet | `<U>Ping</U=db>` | Ping from CB signals next available slot for Tablet |
| Tablet -> CB | `<U>ackCAN 1</U=aa>` | Tablet acknowledges successful receipt of the previous `getCAN` message |


This sequence repeats indefinitely, keeping the tablet and control box in sync with each other.

If the tablet needs to update a register, it will do so in a `setCAN` message.  If the Control Box has any status updates to relay, it does this by sending `getCAN` in response to the `setCAN`.

### Firmware announcement handshake

When the CB announces its firmware (register `06`), the tablet replies with
register `07` (all-zero payload) on the same unit. This reply is mandatory;
see [spec/03-session.md §3.3](spec/03-session.md).

# Register Definitions

The normative register catalog is [spec/04-registers.md](spec/04-registers.md).
Summary:

| Register | Name | Direction | Summary |
| --- | --- | --- | --- |
| `01` | Zone Config (JZ6/JZ7) | both | Zone count, constant zones, filter flag |
| `02` | Unit Type / Activation (JZ*) | CB → Tab | AC brand, activation status, dictionary FW |
| `03` | Zone State (JZ11) | both | Open/close + damper %, sensor type, set/measured temp |
| `04` | Zone Config (JZ13) | both | Min/max damper, motion status/config, error, RSSI |
| `05` | System Status (JZ5/JZ14/JZ15) | both | Power, mode, fan, set temp, myzone, fresh air, RF id |
| `06` | Firmware / Flush (JZ16/JZ17) | both | Flush trigger (write) / firmware + CB type (read) |
| `07` | Firmware Ack (JZ18) | Tab → CB | All-zero response to every reg-06 announcement |
| `08` | Aircon Error (JZ22) | CB → Tab | 5 ASCII error chars |
| `09` | Activation Code (JZ23) | Tab → CB | Set/unlock code + activation period |
| `0a` | Unit Announcement (JZ24) | CB → Tab | Informs tablet a unit exists |
| `12` | Sensor Pairing (JZ32/JZ33) | both | Sensor UID ↔ zone attachment |
| `13` | Info Byte (JZ35) | CB → Tab | Info byte (partly unverified) |
| `16/17/1d/1e` | — | — | Referenced; formats unverified (likely VAMS) |
| `26` | RF Device Pairing (JZ55) | Tab → CB | RF device type + zone channel |
| `27` | RF Device Calibration (JZ57) | Tab → CB | Calibration control + up/down position |

# Wireless sensor pairing flow

1. Select "pair with sensor" on tablet; UI tells user to push pair button on sensor
2. User pushes pair button on sensor
3. CB radio detects sensor (with 'pairing bit' set - see `rf_temp_sensors/` for more info), and CB then sends `12` message with sensor ID to tablet:
```
<U>Ping</U=db><U>setCAN </U=b2><U>getCAN 1 0703abcde0a00000000000000 0703abcde1201613d400e0000 </U=31>
<U>Ping</U=db><U>ackCAN 1</U=aa>
```
4.  Tablet sends updated zone config, with newly discovered sensor attached to the zone

```
<U>Ping</U=db><U>setCAN 0701abcde1201613d01000000</U=36>
```

The complete flow, including RF-device registration (registers `26`/`27`)
and the state machine, is in [spec/07-flows.md](spec/07-flows.md).

# Error Codes

Two classes of error codes exist — see [spec/06-enums.md §6.14](spec/06-enums.md):

- **CB-originated** (register `08`), e.g. `AA1` (no communication with AC
  unit), `AA2` (multiple unit controllers), `AA4` (no temperature sensors).
- **Tablet-generated diagnostics** that never appear on the bus, e.g. `AA60`
  (VAMS setup), `AA62/AA63` (RAS/SAS ports), `AA64/AA65` (VAMS zone sensor
  allocation), `AA123–AA127` (TSP errors).

From: https://www.advantageair.com.au/statuscodes/

| Code | Description |
| ---- | ----------- |
| AA1 | Communication error between Advantage Air componentry and A/C unit. |
| AA2 | Multiple unit controllers detected. |
| AA3 | Communication error | 
| AA4 | System is not detecting any temperature sensors |
| AA81 | Wall sensor has been detected but either no zone has been allocated or more than one zone has been allocated on a particular sensor. |
| AA82 | Wall sensor has been detected but either no zone has been allocated or more than one zone has been allocated on a particular sensor. |
| AA83 | Wall sensor has been detected but either no zone has been allocated or more than one zone has been allocated on a particular sensor. |
| AA86 | Wireless wall sensor has been detected but has a low battery reading. |
| AA89 | Multiple sensors have been been detected on the same zone. |
