
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

_My cable was wired using the T568A standard. Please be careful when wiring your own cables if you're blindly following the colour codes above._

# Communications Protocol Overview

## Ping messages

When powered up, the Control Box (almost) immediately begins sending `Ping` messages to the serial port.  

Each `Ping` message is followed by approximately one second of dead-time (during which the Tablet can communicate, more on that below).

The messages are wrapped in a curious form of XML. An example of what a Ping message looks like is given below:

> `<U>Ping</U=db>`

Each message from the Control Box is separated from the previous with a `SPACE` (`0x20`) character.

If you connect into a Control Box without any Tablet connected 
you get an endless sequence of these `Ping` messages (with the dead-time between messages as mentioned above):

> `<U>Ping</U=db> ... 1 second ... <U>Ping</U=db>  ... 1 second ... <U>Ping</U=db> ... 1 second ... <U>Ping</U=db> ...`


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

```
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

# Control Box Operation

I have found it helpful to imagine of the Control Box as having a set registers, like mailboxes that can be written to and read from.  Each register can hold 7-bytes of data.

The registers control the parameters for your AC system, or lights, or whatever else you have connected to the AA Control Box.

Registers are written to the Control Box using `setCAN` messages, and the Control Box sends updates to registers back to the tablet using `getCAN` messages.

Registers are located hierarchically,

- type of unit being controlled (lights, aircon)
  - unique id of control box
    - register ID

# Basic Packet Structure

An example CAN packet is below, along with a breakdown of the locators used:

> `setCAN 0701abcde1201234501000000`

This message can be broken up into separate parts:

> The `setCAN ` Message means that the **Tablet** is *writing* a register on the Control Box.

> `07` Means that at the highest level, the message relates to Air Conditioning (`0x02` is related to Lights).

> `01` Means that the message is destined for the Control Box (`01`). `03` = Destined for Tablet.

> `abcde` is the unique identifier of the Control Box to send to. Multiple Control Boxes can be chained together, and this field uniquely identifies the correct CB to send to.

> `12` is the register ID (in this case a change in register `0x12` tells the control box that a sensor is being assigned to a zone).  See below for known register definitions.

> `01234501000000` this is 7-bytes of data to be transferred to/from the register (in this case, the data means that sensor id `012345` was attached to Zone #1).  

The purpose of the message flow between the tablet and the Control Box is to synchronise the content of all registers.  The Tablet can send register write messages to the Control Box, and the Control Box in turn notifies the tablet of any changes in values.

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
- implementing myauto/mytemp features
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
| CB -> Tablet | `<U>getCAN 1 0703abcde0a00000000000000 0703abcde0120030101000000 0703abcde0501010330000100 0703abcde0841413400000000 0703abcde1300000000000000 0703abcde0301e40030000000 0703abcde0401006400010000 0703abcde0302640030000000 0703abcde0402146400010000 0703abcde0303e40030000000 0703abcde0403006400010000 0703abcde0304640030000000 0703abcde0404006400010000 0703abcde0305640030000000 0703abcde0405006400010000 0703abcde0306640030000000 0703abcde0406006400010000 0703abcde0307640030000000 0703abcde0407006400010000 0703abcde0308640030000000 0703abcde0408006400010000 0703abcde0309640030000000 0703abcde0409006400010000 0703abcde030a640030000000 0703abcde040a006400010000 0703abcde0211001116000000 </U=d8>` | Initial register status dump |
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

# Register Definitions

## `01` - (Tablet to CB) - Zone Config

| Byte # |  Description |
| --- | ----------- |
| 0   | Hex 0x11 (Decimal 17) -- not sure what this means |
| 1   | # of zones |
| 2   | # of constant zones (0-3) |
| 3   | constant zone 1 |
| 4   | constant zone 2 |
| 5   | constant zone 3 |
| 6   | filter clean status (00 or 01) |


## `01` - (CB to Tablet) - Zone Config

| Byte # | Description |
| --- | ----------- |
| 0   | Hex 0x20 -- not sure what this means or why it is different from above | 
| 1   | # of zones |
| 2   | # of constant zones |
| 3   | constant zone 1 |
| 4   | constant zone 2 |
| 5   | constant zone 3 |
| 6   | filter clean status (00 or 01) |

Example Message:

`07 03 abcde 01 20 03 01 01 00 00 00`

- `07` aircon message
- `03` from CB unit to Tablet
- `abcde` Unit ID 
- `01` zone config message
- `20` (?) -- no idea what this means
- `03` # of zones
- `01` # of constant zones
- `01` constant zone 1 = 1
- `00 00` constant zones 2&3 = unused with only one constant zone.
- `00` filter clean status = `00`


## `02` - Unit type / Activation Status

| Byte # | Description |
| --- | ----------- |
| 0   | Unit Type (hex 0x11=Daikin, 0x12=Panasonic, 0x13=Fujisu, 0x19 = Samsung DVM) |  
| 1   | Activation Status (0=nocode, 1=expired, 2=codeEnabled) |

Note: _Activation_ is a feature that installers can make use of, whereby the system will work for a set number of days after which it locks and requires the user to enter a code to proceed.  Presumably this is to provide an incentive for customers
to pay their bills. Register `09` is used for setting the activation code and/or unlocking a locked system (assuming you know the activation code).

## `03` - CB JZ11 - Zone State

| Byte # |Description |
| --- | ----------- |
| 0   | Zone # (01-0a) |
| 1   | Bit 7: 1=Zone Open, 0=Zone Closed<br>Bits 6-0: Zone Percent 0-100 |
| 2   | Sensor Type<br>0=No Sensor, 1=RF, 2=Wired, 3=RF2CAN Booster, 4=RF_X|
| 3   | Hex Set Temp * 2.0  (0 - 80 ==> 0-40 degrees C)|
| 4   | Measured Temp Int Portion |
| 5   | Measured Temp Decimal Portion (0-9) |
| 6   | Hex 00 / Ignored |

Note: The measured temp and sensor type section of zone state will only be populated after the tablet has sent the control box a `12` message indicating that it has a sensor attached.

It seems that the tablet stores this 'pairing' information in a DB which is local to the MyPlace app.  I think that the easiest way to handle this from an API perspective would be to use a config file (or similar local DB), and provide a mechanism for displaying "sensor pairing button pressed" messages for the user to see.  Maybe a separate app just for doing that.


## `04` - CB JZ13 - Zone Config

| Byte # | Description |
| --- | ----------- |
| 0   | Zone # (`01`-`0a`) |
| 1   | Min Damper |
| 2   | Max Damper |
| 3   | Motion Status (0-22) |
| 4   | Motion Config (0, 1, 2) |
| 5   | Motion Zone Error |
| 6   | CB RSSI |

## `05` - CB JZ14 - System Status

| Byte # | Description |
| --- | ----------- |
| 0   | System State - On (`01`) or off (`00`) |
| 1   | System Mode (`01`=cool,`02`=heat,`03`=vent,`04`=auto,`05`=dry,`06`=myauto) |
| 2   | System Fan (`00`=off, `01`=low, `02`=medium, `03`=high, `04`=auto, `05`=autoAA) |
| 3   | Set Temp (deg C * 2.0) |
| 4   | MyZone ID (1-10, 0 = default / not enabled??) |
| 5   | Fresh Air Status (`00`=none, `01`=off, `02`=on) |
| 6   | RF Sys ID |

CB to Tablet example:

`07|03|abcde|05|01010330000100`
- `01` = System On
- `01` = Cool
- `03` = High
- `30` = 24 degrees (48 / 2.0)
- `00` = no my zone / my zone not enabled
- `01` = Fresh air = on
- `00` = RF Sys ID 0

Notes on MyZone/MyTemp/MyAuto:

The control box seems to determine whether to set a "MyZone" zone based on a few factors.  In the case of the Daikin unit I have, the following needs to happen before a non-zero MyZone ID is sent by the Control Box:

- Control box DIP switch no. 5 needs to be turned off.  The MyAir installation manual says ?switch no. 5 must be ON to use the Return Air Sensor OR in the OFF position to use a MyZone Sensor."
- the field settings in the daikin indoor unit need to be set:
   
| Menu | Setting | Value | Description |
| ---- | ------- | ----- | ----------- |
| 20   |  2      | `03`  | Priority of thermistor sensors for space temperature control. <br/><br/> `01` = The return air thermistor is primary and the remote controller thermistor is secondary.<br/> `02` = Only the return air thermistor will be utilized. <br/> `03` = Only the remote controller thermistor will be utilized.   |
| 22   |  6      | `01`  | The remote controller thermistor is used in Remote Controller Group. <br/><br/> `01` = No <br/> `02` = Yes  |

The MyAir installation manual provides additional details of how to configure these settings.

The MyZone menu options (myzone/mytemp/myauto) do not show up in the user interface until the above conditions have been met, and the control box has started sending a non-zero myzone ID back to the tablet.

I believe that mytemp/myauto are just trickery on behalf of the tablet, automatically moving the myzone around and/or changing the heating/cooling mode.

## `06`(a) - CB to Tablet: CB Firmware Version / Status Message

| Byte # |Description |
| --- | ----------- |
| 0   | CB FW Major |
| 1   | CB FW Minor |
| 2   | CB Type |
| 3   | RF FW Major |
| 4-6   | 000000 |

## `06`(b) - Tablet to CB: Request register flush

| Byte # | Description |
| ---  | ----------- |
| 0-6  | 00000000000000 (all zero's) |

When sent from the tablet to the CB, the `06` register seems to trigger a flush of all registers (at least most registers) back to the control box.

Note, when used in this form, the unit ID is normally all zero's, which I guess means applies to all connected control boxes.


## `07` - CB JZ18 - Tablet to CB: Response to status?

The tablet seems to write to register `07` as a response to the `06` system status message.
Scratch that.  I'm not sure under what circumstances the tablet writes an 07.  Seems that
in response to 06 might be _one_ option, but these also seem to be sent unsolicited at times.
The 07 messages do seem to include the unitId of the airCon.



| Byte # | Description |
| ---  | ----------- |
| 0-6  | 00000000000000 (all zero's) |

## `08` - CB-JZ22 AirCon Error

Register `08` is used to communicate errors from the Control Box to Tablet.

An example would be `AA1` (no connection to air con system).

| Byte # | Description |
| --- | ----------- |
| 0   | Error Char 0 ASCII |
| 1   | Error Char 1 ASCII |
| 2   | Error Char 2 ASCII |
| 3   | Error Char 3 ASCII |
| 4   | Error Char 4 ASCII |
| 5-6 | 0000 |


## `09` - CB-JZ23 - Activation Code Entry

| Byte # | Description |
| --- | ----------- |
| 0   | Action (1 = set new code, 2 = unlock) |
| 1-2 | Unlock Code |
| 3   | Activation Time (days) |
| ??  | ??  | ?? |

## `0a` - CB JZ24 - Set UID (?)

No payload - this is a notice to the tablet that an aircon unit exists with the given UID.

## `12` - CB To Tablet: CB JZ33 - Sensor Pairing Notification; Sensor has been detected

| Byte # |  Description |
| --- | ----------- |
| 0-2 | Sensor UID |
| 3   | Info Byte (bit 6 set == 0x40) |
| 4   | Sensor Major Rev (my sensors are 0x0e) |
| 5,6 | Hex 0000  |

## `12` - Tablet to CB: CB JZ32 - Attach sensor to zone

| Byte # | Description |
| --- | ----------- |
| 0-2 | Sensor UID  |
| 3   | Zone #      |
| 4-6 | Hex 000000  |


## `13` - CB JZ35 - Info Byte (?)

| Byte # | Description |
| --- | ----------- |
| 0   | Info Byte (?) |


# Wireless sensor pairing flow

1. Select "pair with sensor" on tablet; UI tells user to push pair button on sensor
2. User pushes pair button on sensor
3. CB radio detects sensor (with 'pairing bit' set - see `rf_temp_sensor.md` for more info), and CB then sends `12` message with sensor ID to tablet:
```
<U>Ping</U=db><U>setCAN </U=b2><U>getCAN 1 0703abcde0a00000000000000 0703abcde1201613d400e0000 </U=31>
<U>Ping</U=db><U>ackCAN 1</U=aa>
```
4.  Tablet sends updated zone config, with newly discovered sensor attached to the zone

```
<U>Ping</U=db><U>setCAN 0701abcde1201613d01000000</U=36>
<U>getCAN 1 </U=00>
<U>Ping</U=db><U>ackCAN 1</U=aa>
```

5. Control Box sends update with new temperature data for zone

```
<U>Ping</U=db><U>setCAN </U=b2><U>getCAN 1 0703abcde0a00000000000000 0703abcde0301e4012a180200 0703abcde0401006400010029 0703abcde0302640030000000 </U=b0>
<U>Ping</U=db><U>ackCAN 1</U=aa>
```

# Error Codes

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
