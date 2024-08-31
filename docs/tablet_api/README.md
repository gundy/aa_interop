# Tablet API

This document describes the HTTP API exposed by the tablet, and presumably is what the phone app uses to communicate with the system when connected to a local network. This is the API used by other integrations, such as Home Assistant etc.

Reproduced from here: [https://www.domoticz.com/forum/viewtopic.php?t=18555](https://www.domoticz.com/forum/viewtopic.php?t=18555).

## About

This is the API documentation for the MyPlace system by Advantage Air, this allows third parties to connect and control the airconditiong functions of a MyPlace system within a simple home network.

The Wall Mounted Touch Screen must have the latest versions of the following apps - AAConfig, AAService and MyPlace from the Google Play Store.

## Terminology

`Aircon` - one air conditioning unit and associated zones.

`Zone` - on a ducted aircon a zone is a vent or multiple vents to which the airflow is controlled via a motor.

`System` - a system is a collection of air conditioners - currently we support up to 4 aircons.

`Wall Mounted Touch Screen` - the wired android tablet on the wall that controls the system.

## Prerequisites

### 1. Connectivity

The Wall Mounted Touch Screen needs to be connected and have a reliable WiFi connection to the router.

We suggest that the router is connected to the internet to allow Google Play Store updates.

### 2. Discovery

We do not provide a method for discovering the IP address of the Wall Mounted Touch Screen. For the rest of the document we will use 10.0.0.10 as the Wall Mounted Touch Screen IP address.

We suggest that you configure the router to provide the Wall Mounted Touch Screen with a "static" IP address.

## API details

## Read aircon data

Tip: The following commands can be tested using any standard browser.

To get the system data as a single JSON file - use a http GET command on port `2025`.

```sh
GET http://10.0.0.10:2025/getSystemData
```

Here is a heavily edited response to show the relevant data:

```json
{
    "aircons": {
        "ac1": {
            "info": {
                "constant1":1, // Readonly - Constant zone 1 - the system will decide if this zone needs to be automatically opened to protect the ductwork (0 - disabled)
                "constant2":2, // Readonly - Constant zone 2 - the system will decide if this zone needs to be automatically opened to protect the ductwork (0 - disabled)
                "constant3":0, // Readonly - Constant zone 3 - the system will decide if this zone needs to be automatically opened to protect the ductwork (0 - disabled)
                "countDownToOff": 0, // Number of minutes before the aircon unit switches off (0 - disabled)
                "countDownToOn": 0, // Number of minutes before the aircon unit switches on (0 - disabled)
                "fan": "high", // Fan speed - can be "low", "medium" or "high". Note some aircon units also support "auto".
                "freshAirStatus": "none", // Fresh Air status - can be set to "on" or "off". Note: not many aircon units have this fitted.
                "mode": "heat", // Mode - can be "heat", "cool" or "fan". Note some aircon units support "dry".
                "myZone": 0, // MyZone settings - can be set to any zone that has a temperature sensor (0 - disabled)
                "name": "AirconHome", // Name of aircon - max 12 displayed characters
                "setTemp": 24.0, // Set temperature of the aircon unit - this will show the MyZone set temperature if a MyZone is set.
                "state": "on" // Aircon unit state - whether the unit is "on" or "off".
            },
            "zones": {
                "z01": {
                    "name": "FREEGGVFUX", // Name of zone - max 12 displayed characters
                    "setTemp": 25.0, // Set temperature of the zone - only valid when Zone type > 0.
                    "state": "open", // State of the zone - can be "open" or "close". Note: that the
                    "type": 0, // Readonly - Zone type - 0 means percentage (use value to change), any other number means it's temperature control, use setTemp.
                    "value": 20 // Percentage value of zone - only valid when Zone type = 0.
                }
            }
        }
    },
    "system":{
        "name":"MyPlaceSystem", // Name of system - max 12 displayed characters
        "needsUpdate":false,    // If true, you need to prompt user to update the apps on the Wall Mounted Touch Screen
        "noOfAircons":1         // Number of aircon units - this can be 0-4.
    }
}
```

## Sending a command to a single aircon

Tip: The following commands can be tested using any standard browser.

The set command uses a subset of the JSON structure from the getSystem command. However each command can only target one aircon unit. If you have multiple aircons you will have to send one command message per aircon.

### Example aircon unit commands

#### To set the first aircon (ac1) state on or off use the following:

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "info" : { "state": "on" } } } }
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "info" : { "state": "off" } } } }
```

> note: yes, it makes me twitch that HTTP GET requests are being used to update state.

#### To set the second aircon (ac2) mode to heating (heat) use the following:

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "info" : { "mode": "heat" } } } }
```

#### You can also combine messages, so to set aircon ac1 to state=on and mode=cool

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "info" : { "state": "on", "mode": "cool" } } } }
```

## Example zone commands

#### To set the first aircon (ac1), second zone (z02) state to open.

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "zones" : { "z02": { "state": "open" } } } } }
```

#### To set the third aircon (ac3), tenth zone (z10) value to 80%.

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac3": { "zones" : { "z10": { "value": 80 } } } } }
```

#### To set the second aircon (ac2), eighth zone (z8) value to 24 degrees.

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac2": { "zones" : { "z08": { "setTemp": 24 } } } } }
```

#### For a combination of settings you can use the one command

```sh
GET http://10.0.0.10:2025/setAircon?json={"aircons": { "ac1": { "zones" : { "z01": { "setTemp": 22 } } } } }
```
