#!/usr/bin/python
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import os
import logging
import socket
from time import sleep
import sys

logger = None
MAX_BLOB_SIZE = 10 * 1024

blobstore = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
blobstore.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir + "/../db/", 'blobstore.sqlite')
db = SQLAlchemy(blobstore)

class Blobs(db.Model):
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.LargeBinary)

db.create_all()

def _writeToPIDFile(p_num):
    with open(basedir + "/../pids/pid-{0}.pid".format(p_num), "w") as fp:
        fp.write(str(os.getpid()))

def _initializeLogger(p_num):
    global logger
    logFileName = basedir + "/../logs/blobstore-{0}.log".format(p_num)
    logger = logging.getLogger("BlobStoreLogger")
    logger.setLevel(logging.INFO)
    fileHandler = logging.FileHandler(logFileName)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

@blobstore.route("/")
def home():
    return "HELLO WORLD!\n"

@blobstore.route("/store/<blobKey>", methods=["GET", "POST", "PUT", "DELETE"])
def blob_ops(blobKey):
    retCode = 200
    retVal = ''
    logger.info("REQUEST RECEIVED: type = {0}, key = {1}" \
              .format(request.method, blobKey))

    blobValue = request.get_data()
    if len(blobValue) > MAX_BLOB_SIZE:
        logger.error("Blob with key={0} exceeds the max size of {1}." \
                   .format(len(blobValue), MAX_BLOB_SIZE))
        retCode = 413
        retVal = "Failed to insert the blob={0} because of size limitations." \
                 " Blob size = {1}, Max allowed size = {2}". \
                 format(blobKey, len(blobValue), MAX_BLOB_SIZE)
        return retVal, retCode

    if request.method == 'POST':
        blob = Blobs(key = blobKey, value = blobValue)
        try:
            db.session.add(blob)
            db.session.commit()
            retVal = "Successfully inserted blob={} into blobstore.\n".format(blobKey)
        except sqlalchemy.exc.IntegrityError, e:
            logger.error("Blob with key={0} already exists.".format(blobKey))
            db.session.rollback()
            retCode = 403
            retVal = "Blob={0} already exists in the blobstore.".format(blobKey) 
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
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
            retCode = 500
            retVal = "Failed to query blob={0} from blobstore. Error={1}\n". \
		     format(blobKey, e.message)
    elif request.method == 'PUT':
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
                retVal = "Successfully deleted blob={0} in blobstore. Current blob" \
                         " count with key={0} is {1}\n". \
		format(blobKey, blobCount)
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
            retCode = 500
            retVal = "Failed to delete blob={0} from blobstore. Error={1}\n". \
		     format(blobKey, e.message)

    return retVal, retCode

def runBlobStore():
    try:
        blobstore.run(host='0.0.0.0', port=7777, debug = True)
    except socket.error, e:
        if e.errno == 98:
	    logger.debug("Another instance blobstore service bound itself to the port.")
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
