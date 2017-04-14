#!/bin/bash
BLOBSTORE_DIR=$HOME/fault-tolerant-storage-solution
MONITRC_DIR=/etc/monit/

# Check the user
USER=$(whoami)
if [ $USER != "root" ]; then
    echo "This script needs to be run as root user."
    exit 1
fi

# Check if python interpreter is available
python --version
if [ $? -ne 0 ]; then
    echo "Install python >= 2.7"
    exit 2
fi

# Install all the required packages.
apt-get update
apt-get -y install python-pip
pip install Flask
pip install Flask-SQLAlchemy
apt-get -y install monit

# Packages needed for running test cases
pip install psutil
pip install requests

# Establish the required symbolic links
ln -sf $BLOBSTORE_DIR/conf/blobstoremonitrc $MONITRC_DIR/conf-enabled/
ln -sf $BLOBSTORE_DIR/bin/blobstore.sh /bin/
ln -sf $BLOBSTORE_DIR/conf/monitrc $MONITRC_DIR
ln -sf $BLOBSTORE_DIR/pids/ /var/run/blobstore_pids

# Set the right permissions
chmod 700 $BLOBSTORE_DIR/conf/monitrc
