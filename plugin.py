# Disc Usage Python Plugin
#
# Author: Xorfor
#
"""
<plugin key="xfr_discusage" name="Disc usage" author="Xorfor" version="1.2.0" externallink="https://github.com/Xorfor/Domoticz-Disc-usage-Plugin">
    <params>
        <param field="Address" label="Device" width="200px" required="true"/>
        <param field="Mode2" label="Minutes between check" width="100px" required="true" default="60"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import platform
import os


class BasePlugin:

    __MINUTE = 6

    __ACTIVE = 0
    __TIMEDOUT = 1

    __DEBUG_OFF = 0
    __DEBUG_ON = 1

    __UNIT_USAGE = 1
    __UNIT_FREE = 2
    __UNIT_SIZE = 3
    __UNIT_USED = 4

    __UNITS = [
        # Unit, Name, Type, Subtype, Options, Used
        [__UNIT_USAGE, "{} - usage", 243, 31, {"Custom": "0;%"}, 1],
        [__UNIT_FREE, "{} - available", 243, 31, {"Custom": "0;K"}, 1],
        [__UNIT_SIZE, "{} - size", 243, 31, {"Custom": "0;K"}, 1],
        [__UNIT_USED, "{} - used", 243, 31, {"Custom": "0;K"}, 1],
    ]

    def __init__(self):
        self.__platform = platform.system()
        self.__debug = self.__DEBUG_OFF
        self.__runAgain = 0
        self.__COMMAND = ""
        self.__OPTIONS = ""
        self.__factor = None
        self.__options = None

    def onStart(self):
        Domoticz.Debug("onStart called")
        #
        # Debugging On/Off
        if Parameters["Mode6"] == "Debug":
            self.__debug = self.__DEBUG_ON
        else:
            self.__debug = self.__DEBUG_OFF
        Domoticz.Debugging(self.__debug)
        #
        # Platform independent commands
        Domoticz.Debug("Platform: "+self.__platform)
        if self.__platform == "Linux":
            self.__COMMAND = "df"
            self.__OPTIONS = "{} --block-size=1K --output=target,avail,size"
        elif self.__platform == "Windows":
            self.__COMMAND = "wmic"
            self.__OPTIONS = "logicaldisk {} get caption, freespace, size"
        #
        # Create devices
        if len(Devices) == 0:
            for unit in self.__UNITS:
                Domoticz.Device(Unit=unit[0],
                                Name=unit[1].format(Parameters["Address"]),
                                Type=unit[2],
                                Subtype=unit[3],
                                Options=unit[4],
                                Used=unit[5],
                                Image=3
                                ).Create()

        # if (_UNIT_USAGE not in Devices):
        #     # Unfortunately the image in the Percentage device can not be changed. Use Custom device!
        #     # Domoticz.Device(Unit=_UNIT_USAGE, Name=Parameters["Address"], TypeName="Percentage", Used=1).Create()
        #     Domoticz.Device(Unit=_UNIT_USAGE, Name=Parameters["Address"], TypeName="Custom", Options={"Custom": "1;%"}, Image=3, Used=1).Create()
        # else:
        #     Devices[_UNIT_USAGE].Update(nValue=0, sValue=str(0), TimedOut=_TIMEDOUT)
        #
        # Global settings
        DumpConfigToLog()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) +
                       ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text +
                       "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        if self.__runAgain <= 0:
            found = False
            # Execute command
            ret = os.popen(self.__COMMAND + " " +
                           self.__OPTIONS.format(Parameters["Address"])).read()
            for line in ret.splitlines():
                Domoticz.Debug("Line: " + str(line))
                data = line.split()
                Domoticz.Debug("Device: " + data[0])
                Domoticz.Debug("Freespace: " + data[1])
                Domoticz.Debug("Size: " + data[2])
                if data[0] == Parameters["Address"]:
                    found = True
                    Domoticz.Debug("Found " + Parameters["Address"])
                    freespace = int(data[1])
                    size = int(data[2])
                    Domoticz.Debug("freespace: {}".format(freespace))
                    Domoticz.Debug("size: {}".format(size))
                    #
                    if size > 0:

                        self.__factor = 1
                        self.__options = {"Custom": "0;K"}
                        if size > 10**5:
                            self.__factor = 2**10
                            self.__options = {"Custom": "0;M"}
                        if size > 10**8:
                            self.__factor = 2**20
                            self.__options = {"Custom": "0;G"}
                        if size > 10**11:
                            self.__factor = 2**30
                            self.__options = {"Custom": "0;T"}
                        Domoticz.Debug("factor: {}".format(self.__factor))
                        Domoticz.Debug("options: {}".format(self.__options))

                        usage = round((size - freespace) * 100 / size, 2)
                        UpdateDevice(self.__UNIT_USAGE,
                                     int(usage),
                                     str(usage),
                                     self.__ACTIVE
                                     )

                        UpdateDeviceOptions(self.__UNIT_FREE, self.__options)
                        UpdateDevice(self.__UNIT_FREE,
                                     int(freespace / self.__factor),
                                     str(round(freespace / self.__factor, 1)),
                                     self.__ACTIVE
                                     )

                        UpdateDeviceOptions(self.__UNIT_SIZE, self.__options)
                        UpdateDevice(self.__UNIT_SIZE,
                                     int(size / self.__factor),
                                     str(round(size / self.__factor, 1)),
                                     self.__ACTIVE
                                     )
                        used = size - freespace

                        UpdateDeviceOptions(self.__UNIT_USED, self.__options)
                        UpdateDevice(self.__UNIT_USED,
                                     int(used / self.__factor),
                                     str(round(used / self.__factor, 1)),
                                     self.__ACTIVE
                                     )
            if not found:
                Domoticz.Debug("Device '{}' not found!!!".format(
                    Parameters["Address"]))
            self.__runAgain = self.__MINUTE * int(Parameters["Mode2"])
        else:
            Domoticz.Debug(
                "onHeartbeat, run again in {} heartbeats".format(self.__runAgain))


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

################################################################################
# Generic helper functions
################################################################################


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))


def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if Unit in Devices:
        if Devices[Unit].nValue != nValue or Devices[Unit].sValue != sValue or Devices[Unit].TimedOut != TimedOut or AlwaysUpdate:
            Devices[Unit].Update(nValue=nValue,
                                 sValue=str(sValue),
                                 TimedOut=TimedOut
                                 )
            Domoticz.Debug(
                "Update {}: {} - '{}'".format(
                    Devices[Unit].Name,
                    nValue,
                    sValue
                )
            )


def UpdateDeviceOptions(Unit, Options={}):
    if Unit in Devices:
        if Devices[Unit].Options != Options:
            Devices[Unit].Update(nValue=Devices[Unit].nValue,
                                 sValue=Devices[Unit].sValue,
                                 Options=Options
                                 )
            Domoticz.Debug("Device Options update: {} = {}".format(
                Devices[Unit].Name,
                Options
            )
            )
