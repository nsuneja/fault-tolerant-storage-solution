#!/bin/bash

BLOBSTORE_DIR=$HOME/fault-tolerant-storage-solution
PIDS_DIR=$BLOBSTORE_DIR/pids
LOGS_DIR=$BLOBSTORE_DIR/logs/

log() {
    echo `date`" $@" >> $LOGS_DIR/blobstore.log 
}

start() {
    p_num=$1
    nohup $BLOBSTORE_DIR/blobstore.py $p_num > /dev/null 2>&1 &
    if [ $? -ne 0 ]; then
        log "Failed to start blobstore instance: $p_num"
        exit 3
    fi
}

stop() {
    p_num=$1
    PID=$(cat $PIDS_DIR/pid-$p_num.pid)
    kill -TERM $PID
    if [ $? -ne 0 ]; then
        log "Failed to stop blobstore instance: $p_num. No such process."
    fi
}

if [[ $# -lt 2 ]]; then
    log "Usage: blobstore.sh <command> <process_num>"
    exit 1
fi

command=$1
p_num=$2

if [[ $command == "start" ]]; then
    start $p_num
elif [[ $command == "stop" ]]; then
    stop $p_num
else
    log "Invalid command. Valid options: <start> | <stop>"
    exit 2
fi

