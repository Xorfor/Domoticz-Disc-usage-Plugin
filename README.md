# Domoticz-Disc-usage-Plugin
Domoticz offers 'Motherboard sensors' which gives some data about CPU Usage, Memory Usage, etc. Also the usage of '/' and '/boot' are given. Because I also wanted to monitor the usage of the discs from my NAS, I wrote this plugin.
## Warning
This is still beta!!!
I check the platform on which Domoticz is running. Depending on the platform (Linux or Windows), different commands are used. Until now the plugin is only tested on a Raspberry Pi, but it also should work on Windows.
## Parameters
| Parameter | Value |
| :--- | :--- |
| **Device**  | eg. /mnt/Backup (on Linux), or C: (on Windows) |
| **Minutes between check**  |  default is 60  |
## Todo
- [ ] Get it tested on Windows
- [x] ~~Move Mode1 to Address, so that in the device list the devices are directly visible~~
