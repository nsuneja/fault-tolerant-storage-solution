BLOBSTORE_DIR=$HOME/fault-tolerant-storage-solution
MONITRC_DIR=/etc/monit/

# Install all the required packages.
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
