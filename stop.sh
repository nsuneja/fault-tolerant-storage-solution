#!/bin/bash
# Check the user
USER=$(whoami)
if [ $USER != "root" ]; then
    echo "This script needs to be run as root user."
    exit 1
fi

# Stop the blobstore service group
monit -g blobstore stop

# Stop monit daemon
monit quit
