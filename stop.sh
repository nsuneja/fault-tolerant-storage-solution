# Stop the blobstore service group
monit -g blobstore stop

# Stop monit daemon
monit quit
