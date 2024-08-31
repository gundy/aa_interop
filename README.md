# Overview

This repository contains a set of working notes relating to the AA "MyAir" / "MyPlace" controller, with a particular focus on the communication between the Control Box, and the Tablet / Temperature Sensors. The intent of this work is to enable interoperability with other systems.

This documentation has been researched and written over many a late night, and discovered largely through trial and error. It is probably wrong in multiple places. Use it with caution.

It has also required a reasonable investment of my own money in parts and equipment. If you value this work, please consider sharing it and contributing to it. If you use it, please link back to the source, and if you modify it, please share your work so others can also benefit (and/or raise a pull request against this repo).

This documentation is released under the [GNU Free Documentation License v1.3](./LICENSE.md) and comes with [some warnings and disclaimers](./WARNING.md).

# The documentation

The documentation is split into sections:

* Tablet to Control Box communications: [`docs/cb_tablet_comms/README.md`](./docs/cb_tablet_comms/README.md),  
* RF Temperature Sensor communications: [`docs/rf_temp_sensors/README.md`](./docs/rf_temp_sensors/README.md), including GNU Radio flow graph for monitoring sensor output.
* HTTP API exposed by the tablet for controlling the system: [`docs/tablet_api/README.md`](./docs/tablet_api/README.md).

# Limitations

The information contained in this repository has all been learnt by monitoring a single unit, a CB9 control box, and it's associated peripherals. Before relying on any information contained herein, please verify against your own unit. Read [WARNING.md](./WARNING.md) for additional warnings before proceeding to use any information in this documentation.

# Goals

The goals of this work are:

- To create a set of documentation that ultimately enables interoperation and integration between the AA system and a wider range of open source home automation software (eg. OpenHAB, HomeKit, ...), and connectivity with open hardware.
- To safeguard against failure or eventual obsolescence of the AA Android tablet (eg. [through worn out flash storage](https://blog.hopefullyuseful.com/blog/advantage-air-ezone-tablet-diy-repair/)).

# Why?

- If the tablet ever dies, [for whatever reason](https://blog.hopefullyuseful.com/blog/advantage-air-ezone-tablet-diy-repair/), the air conditioning unit becomes non-functional. In my household that would be classed as a very-high-severity incident!
- I just prefer my "critical-infrastructure" to be relatively "dumb". And open/easy to repair.

Dave Jones from EEVBlog covers some other reasons to be skeptical of vendor-supplied internet-requiring smart devices here:

https://www.youtube.com/watch?v=zc7wmT72C-w

# You probably don't need this documentation

The tablet already exposes an API that can be used to control the AC system, and [eg. connectors to Home Assistant](https://www.home-assistant.io/integrations/advantage_air/) have already been built on top of this API.  

If the Tablet in your system is still working, and you're otherwise happy with it, you will be well served by leaving it alone and/or using pre-existing integrations for things like HomeAssistant integration.
