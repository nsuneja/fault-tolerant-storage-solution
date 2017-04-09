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

@blobstore.route("/store/<blob_key>", methods=["GET", "POST", "PUT", "DELETE"])
def blob_ops(blob_key):
    retCode = 200
    retMsg = ''
    if request.method == 'POST':
        blob_value = request.get_data()
        blob = Blobs(key = blob_key, value = blob_value)
        try:
            db.session.add(blob)
            db.session.commit()
            retMsg = "Successfully inserted blob={} into blobstore.\n".format(blob_key)
        except Exception, e:
            logger.exception(e)
            db.session.rollback()
            # TODO: Make the error code exception specific.
            retCode = 500
            retMsg = "Failed to insert blob={0} into blobstore. Error={1}\n". \
		     format(blob_key, e.message)
	  
    return retMsg, retCode

if __name__ == "__main__":
    _initializeLogger()
    blobstore.run(debug=True)
