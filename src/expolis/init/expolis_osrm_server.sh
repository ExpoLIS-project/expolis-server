#!/usr/bin/env sh

### BEGIN INIT INFO
# Provides:          expolis_osrm_server
# Required-Start:    $local_fs $network
# Required-Stop:     $local_fs $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: ExpoLIS OSRM server
# Description:       Start the ExpoLIS OSRM server
#  This script will start the ExpoLIS OSRM server.
### END INIT INFO

python3 /opt/expolis/bin/osrm_server.py "$@"
