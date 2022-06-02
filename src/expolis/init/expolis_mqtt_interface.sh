#!/usr/bin/env sh

### BEGIN INIT INFO
# Provides:          expolis_mqtt_interface
# Required-Start:    $syslog $remote_fs $network
# Required-Stop:     $syslog $remote_fs $network
# Default-Start:     3 5
# Default-Stop:      0 1 6
# Short-Description: ExpoLIS MQTT interface
# Description:       Start the ExpoLIS MQTT interface
#  This script will start the ExpoLIS MQTT interface.
### END INIT INFO

python3 /opt/expolis/bin/mqtt_interface.py "$@"
