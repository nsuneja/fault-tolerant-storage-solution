#!/usr/bin/python
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import os
import logging
import socket
from time import sleep
import sys
import os

logger = None

blobstore = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
blobstore.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blobstore.sqlite')
db = SQLAlchemy(blobstore)
db.create_all()

class Blobs(db.Model):
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.LargeBinary)

def _writeToPIDFile(p_num):
    with open(basedir + "/pids/pid-{0}.pid".format(p_num), "w") as fp:
        fp.write(str(os.getpid()))

def _initializeLogger(p_num):
    global logger
    logFileName = basedir + "/logs/blobstore-{0}.log".format(p_num)
    logger = logging.getLogger("BlobStoreLogger")
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler(logFileName)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

@blobstore.route("/")
def home():
    return "HELLO WORLD!\n"

@blobstore.route("/store/<blobKey>", methods=["GET", "POST", "PUT", "DELETE"])
def blob_ops(blobKey):
    retCode = 200
    retVal = ''
    if request.method == 'POST':
        blobValue = request.get_data()
        blob = Blobs(key = blobKey, value = blobValue)
        try:
            db.session.add(blob)
            db.session.commit()
            retVal = "Successfully inserted blob={} into blobstore.\n".format(blobKey)
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
            # TODO: Make the error code exception specific.
            retCode = 500
            retVal = "Failed to insert blob={0} into blobstore. Error={1}\n". \
		     format(blobKey, e.message)
    elif request.method == 'GET':
        try:
	    blobs = db.session.query(Blobs).filter_by(key=blobKey)
            if blobs.count() == 0:
                retCode = 404
		retVal = "Blob={0} not found in the blobstore.\n".format(blobKey)
            else:
                retVal = str(blobs.first().value) 
        except Exception, e:
            logger.exception(e)
            # TODO: Make the error code exception specific.
            retCode = 500
            retVal = "Failed to query blob={0} from blobstore. Error={1}\n". \
		     format(blobKey, e.message)
    elif request.method == 'PUT':
        blobValue = request.get_data()
        try:
	    blobs = db.session.query(Blobs).filter_by(key=blobKey)
            if blobs.count() == 0:
                retCode = 404
		retVal = "Blob={0} not found in the blobstore.\n".format(blobKey)
            else:
                blobs.first().value = blobValue
                db.session.commit()
                retVal = "Successfully updated blob={0} in blobstore.\n".format(blobKey)
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
            # TODO: Make the error code exception specific.
            retCode = 500
            retVal = "Failed to update blob={0} in blobstore. Error={1}\n". \
		     format(blobKey, e.message)
    elif request.method == 'DELETE':
        try:
	    blobs = db.session.query(Blobs).filter_by(key=blobKey)
            if blobs.count() == 0:
                retCode = 404
		retVal = "Blob={0} not found in the blobstore.\n".format(blobKey)
            else:
                db.session.delete(blobs.first())
                db.session.commit()
	        blobCount = db.session.query(Blobs).filter_by(key=blobKey).count()
                retVal = "Successfully deleted blob={0} in blobstore. Current blob count={1}\n". \
		format(blobKey, blobCount)
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
            # TODO: Make the error code exception specific.
            retCode = 500
            retVal = "Failed to delete blob={0} from blobstore. Error={1}\n". \
		     format(blobKey, e.message)

    return retVal, retCode

def runBlobStore():
    try:
        blobstore.run(host='0.0.0.0', port=7777)
    except socket.error, e:
        if e.errno == 98:
	    logger.warn("Another instance blobstore service bound itself to the port.")
	else:
	    raise e

if __name__ == "__main__":
    p_num = 0
    if len(sys.argv) > 1:
        p_num = int(sys.argv[1])

    _writeToPIDFile(p_num)
    _initializeLogger(p_num)
    while True:
        runBlobStore()
        sleep(0.1)
