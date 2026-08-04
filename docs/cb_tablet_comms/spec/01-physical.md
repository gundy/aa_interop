# 01 — Physical Layer

## 1.1 Transport

The Control Box (CB) and the tablet communicate over a half-duplex differential
RS-485 serial link.

| Parameter | Value |
|---|---|
| Standard | RS-485 (half-duplex) |
| Baud rate | 57600 |
| Framing | 8 data bits, no parity, 1 stop bit (8N1) |
| Bus direction | Half-duplex; only one station transmits at a time |

## 1.2 Cable / connector

The link runs over an Ethernet-style RJ45 cable between the CB and the tablet.
The same cable also carries ~14 V DC power to the tablet, so pin identification
must be done by pin number, not colour.

| Pin | T568A colour | T568B colour | Signal |
|---|---|---|---|
| 1 | green/white | orange/white | RS-485 B (+) |
| 2 | green | orange | RS-485 A (−) |
| 3 | orange/white | green/white | unused |
| 4 | blue | blue | GND |
| 5 | blue/white | blue/white | ~14 V DC to tablet |
| 6 | orange | green | GND |
| 7 | brown/white | brown/white | unused |
| 8 | brown | brown | unused |
| Shield | | | GND |

## 1.3 Bus ownership

The CB initiates all traffic: it transmits a `Ping` frame approximately once per
second, followed by a dead-time window in which the tablet may transmit exactly
one frame in reply. The tablet must never transmit outside this window.

## 1.4 Interfacing from another host

A USB-to-RS485 adapter (A/B/GND to pins 1/2/4-6) is sufficient to observe or
participate in the bus. The adapter must be configured for 57600 8N1, half-duplex.
The bus carries ~15 V on pin 5 — take care when wiring adapters and grounds.
