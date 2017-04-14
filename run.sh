# Check the user
USER=$(whoami)
if [ $USER != "root" ]; then
    echo "This script needs to be run as root user."
    exit 1
fi

# Start monit daemon
monit

# Start blobstore service group
monit -g blobstore start
