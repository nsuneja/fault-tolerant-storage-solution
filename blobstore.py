#!/usr/bin/python
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import os

blobstore = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
blobstore.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blobstore.sqlite')
db = SQLAlchemy(blobstore)

class Blobs(db.Model):
    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.LargeBinary)

@blobstore.route("/")
def home():
    return "HELLO WORLD!"

@blobstore.route("/store/<blob_key>", methods=["GET", "POST", "PUT", "DELETE"])
def blob_ops(blob_key):
    if request.method == 'POST':
        blob_value = request.get_data()
        blob = Blobs(key = blob_key, value = blob_value)
        db.session.add(blob)
        db.session.commit()

    return '', 200

if __name__ == "__main__":
    db.create_all()
    blobstore.run(debug=True)
