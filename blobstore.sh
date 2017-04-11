#!/bin/bash

BLOBSTORE_DIR=$HOME/fault-tolerant-storage-solution
PIDS_DIR=$BLOBSTORE_DIR/pids

start() {
    p_num=$1
    nohup $BLOBSTORE_DIR/blobstore.py $p_num > /dev/null 2>&1 &
    if [ $? -ne 0 ]; then
        echo "Failed to start blobstore instance: $p_num"
        exit 3
    fi
}

stop() {
    p_num=$1
    PID=$(cat $PIDS_DIR/pid-$p_num.pid)
    kill -TERM $PID
    if [ $? -ne 0 ]; then
        echo "Failed to stop blobstore instance: $p_num. No such process."
    fi
}

if [[ $# -lt 2 ]]; then
    echo "Usage: blobstore.sh <command> <process_num>"
    exit 1
fi

command=$1
p_num=$2

if [[ $command == "start" ]]; then
    start $p_num
elif [[ $command == "stop" ]]; then
    stop $p_num
else
    echo "Invalid command. Valid options: <start> | <stop>"
    exit 2
fi

