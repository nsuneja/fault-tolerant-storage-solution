#!/usr/bin/python
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import os
import logging

blobstore = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
blobstore.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blobstore.sqlite')
db = SQLAlchemy(blobstore)
db.create_all()

class Blobs(db.Model):
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.LargeBinary)

def _initializeLogger():
    global logger
    logFileName = basedir + "/blobstore.log"

    # TODO: Make the log file name unique for each instance of blobstore service.
    logger = logging.getLogger("BlobStoreLogger")
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler(logFileName)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

@blobstore.route("/")
def home():
    return "HELLO WORLD!"

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
	    blobValue = db.session.query(Blobs.value).filter_by(key=blobKey)[0][0]
            retVal = str(blobValue) 
        except Exception, e:
            logger.exception(e)
            # TODO: Make the error code exception specific.
            retCode = 500
            retVal = "Failed to query blob={0} from blobstore. Error={1}\n". \
		     format(blobKey)

    return retVal, retCode

if __name__ == "__main__":
    _initializeLogger()
    blobstore.run(debug=True)
