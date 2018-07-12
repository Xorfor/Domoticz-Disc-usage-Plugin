# Disc Usage Python Plugin
#
# Author: Xorfor
#
"""
<plugin key="xfr_discusage" name="Disc usage" author="Xorfor" version="1.1.0" externallink="https://github.com/Xorfor/Domoticz-Disc-usage-Plugin">
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

_UNIT_USAGE = 1

_MINUTE = 6

_ACTIVE = 0
_TIMEDOUT = 1

_DEBUG_OFF = 0
_DEBUG_ON = 1


class BasePlugin:

    def __init__(self):
        self.__platform = platform.system()
        self.__debug = _DEBUG_OFF
        self.__runAgain = 0
        self.__COMMAND = ""
        self.__OPTIONS = ""
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        #
        # Debugging On/Off
        if Parameters["Mode6"] == "Debug":
            self.__debug = _DEBUG_ON
        else:
            self.__debug = _DEBUG_OFF
        Domoticz.Debugging(self.__debug)
        #
        # Platform independent commands
        Domoticz.Debug("Platform: "+self.__platform)
        if self.__platform == "Linux":
            self.__COMMAND = "df"
            self.__OPTIONS = "--output=target,avail,size"
        elif self.__platform == "Windows":
            self.__COMMAND = "wmic"
            self.__OPTIONS = "logicaldisk get caption, freespace, size"
        #
        # Create devices
        if (_UNIT_USAGE not in Devices):
            # Unfortunately the image in the Percentage device can not be changed. Use Custom device!
            # Domoticz.Device(Unit=_UNIT_USAGE, Name=Parameters["Address"], TypeName="Percentage", Used=1).Create()
            Domoticz.Device(Unit=_UNIT_USAGE, Name=Parameters["Address"], TypeName="Custom", Options={"Custom": "1;%"}, Image=3, Used=1).Create()
        else:
            Devices[_UNIT_USAGE].Update(nValue=0, sValue=str(0), TimedOut=_TIMEDOUT)
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
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.__runAgain -= 1
        found = False
        if self.__runAgain <= 0:
            # Execute command
            ret = os.popen(self.__COMMAND + " " + self.__OPTIONS).read()
            for line in ret.splitlines():
                Domoticz.Debug("Line: "+str(line))
                data = line.split()
                Domoticz.Debug("Device: "+data[0])
                Domoticz.Debug("Freespace: "+data[1])
                Domoticz.Debug("Size: "+data[2])
                if data[0] == Parameters["Address"]:
                    found = True
                    Domoticz.Debug("Found "+Parameters["Address"])
                    freespace = int(data[1])
                    size = int(data[2])
                    if size > 0:
                        usage = round((size-freespace)*100/size, 2)
                        UpdateDevice(_UNIT_USAGE, int(usage), str(usage), _ACTIVE)
            if not found:
                Domoticz.Debug("Device '"+Parameters["Address"]+"' not found!!!")
                UpdateDevice(_UNIT_USAGE, int(0), str(0), _TIMEDOUT)

            self.__runAgain = _MINUTE*int(Parameters["Mode2"])
        else:
            Domoticz.Debug("onHeartbeat called, run again in "+str(self.__runAgain)+" heartbeats.")

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
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

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
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Debug("Update " + Devices[Unit].Name + ": " + str(nValue) + " - '" + str(sValue) + "'")
