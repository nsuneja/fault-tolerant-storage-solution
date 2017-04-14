#!/usr/bin/python
import unittest
import threading
import requests
import os
import time
import traceback
import psutil
import random
from random import choice
from string import ascii_uppercase

BLOBSTORE_PORT = "7777"
BLOBSTORE_HOST = "localhost"
BLOBSTORE_ENDPOINT = "/store/"
BLOBSTORE_URL = "http://" + BLOBSTORE_HOST + ":" + BLOBSTORE_PORT + BLOBSTORE_ENDPOINT
MAX_CONNECTION_ERR_RETRIES = 10
PID_DIR = "/var/run/blobstore_pids/"

class MethodType:
    GET = 0
    POST = 1
    PUT = 2
    DELETE = 3
    

def handleConnectionError(methodType):
    def wrap(f):
        def newFunction(*args, **kw):
            retryCount = 0
            while True:
                try:
                    ret = f(*args, **kw)
                    if methodType == MethodType.GET:
                        # Handle the special case with empty return. Retry...
                        if ret[0] == 200 and ret[1] == '':
                            raise requests.ConnectionError
                    return ret
                except requests.ConnectionError, e:
                    print str(e)
                    # We lost the connection to the server (perhaps because of failure injection).
                    # Give it some time to recover.
                    time.sleep(2)
                    # Handle the case where the
                    # SQL operation went through on the backend, but because of us injecting
                    # a failure by killing the leader, client received a connection error,
                    # and retried the operation, which failed because of the blobKey existing
                    # in the blobstore.
                    if methodType == MethodType.POST:
                        response = requests.get(BLOBSTORE_URL + args[0])
                        if response.status_code == 200:
                            # Original request succeeded. Bail...
                            return 200, ''

                    if methodType == MethodType.DELETE:
                        response = requests.get(BLOBSTORE_URL + args[0])
                        if response.status_code == 404:
                            # Original request succeeded. Bail...
                            return 200, ''
                    
                    retryCount += 1
                    if retryCount > MAX_CONNECTION_ERR_RETRIES:
                        raise e
                    print "RETRYING...({0}/{1})".format(retryCount, MAX_CONNECTION_ERR_RETRIES)
        return newFunction
    return wrap

@handleConnectionError(MethodType.POST)
def post(key, value):
    response = requests.post(BLOBSTORE_URL + key, data = value)
    return response.status_code, response.text

@handleConnectionError(MethodType.GET)
def get(key):
    response = requests.get(BLOBSTORE_URL + key)
    return response.status_code, response.text

@handleConnectionError(MethodType.PUT)
def put(key, value):
    response = requests.put(BLOBSTORE_URL + key, data = value)
    return response.status_code, response.text

@handleConnectionError(MethodType.DELETE)
def delete(key):
    response = requests.delete(BLOBSTORE_URL + key)
    return response.status_code, response.text


class BlobStoreTest(unittest.TestCase):

    def _init(self):
        self.counterKey = "counterKey-{0}".format(self._generateRandomNumber())
        self.counterInitVal = 0
        self.numThreads = 10
        self.iterCount = 100
        self.threadSyncLock = threading.Lock()
        self.injectFailureSignal = threading.Event()
        self.maxBlobSize = 10 * 1024
        self.largeBlobKey = "largeBlobKey-{0}"
        self.largeBlobCounter = 0
        self.largeBlobKeyInitVal = self._generateRandomNumber()


    def _generateRandomNumber(self):
        return long(random.choice(range(0,10000000)))

    
    def _initCounter(self):
        retCode, retVal = post(self.counterKey, str(self.counterInitVal))
        self.assertEqual(retCode, 200)


    def _removeCounter(self):
        retCode, retVal = delete(self.counterKey)
        self.assertEqual(retCode, 200)


    def _incrementCounter(self):
        for i in range(self.iterCount):
            with self.threadSyncLock:
                retCode, retVal = get(self.counterKey)
                self.assertEqual(retCode, 200)
                counter = int(retVal)
                counter += 1
                retCode, retVal = put(self.counterKey, str(counter))
                self.assertEqual(retCode, 200)
                print "Incremented the counter to {0}".format(counter)
            time.sleep(0.1) 


    def _dispatchLargeBlobs(self):
        for i in range(self.iterCount):
            with self.threadSyncLock:
                blobKey = self.largeBlobKeyInitVal + self.largeBlobCounter
                data = ''.join(choice(ascii_uppercase) for i in range(self.maxBlobSize))
                print "Uploading blob-{0}".format(self.largeBlobCounter)
                retCode, retVal = post(self.largeBlobKey.format(blobKey), data)
                self.assertEqual(retCode, 200)
                self.largeBlobCounter += 1
            time.sleep(0.5)


    def _FetchAndDeleteLargeBlobs(self):
        for i in range(self.largeBlobCounter):
            blobKey = self.largeBlobKey.format(self.largeBlobKeyInitVal + i)
            print "Fetching and deleting blob = {0}".format(i)
            retCode, retVal = get(blobKey)
            self.assertEqual(retCode, 200)
            retCode, retVal = delete(blobKey)
            self.assertEqual(retCode, 200)
            time.sleep(0.1)


    def _injectFailure(self):
        # Initial delay.
        time.sleep(5)
        while not self.injectFailureSignal.is_set():
            # Read the pid files and kill process from blobstore process
            # group which is currently listening on the server port.
            for pid_file in os.listdir(PID_DIR):
                with open(PID_DIR + pid_file, 'r') as fp:
                    pid = fp.read()

                try:
                    p = psutil.Process(int(pid))
                    for conn in p.connections():
                        if conn.laddr[1] == int(BLOBSTORE_PORT):
                            # Found the leader. Kill it.
                            print "Blobstore leader is process = {0}. Killing it...".format(pid)
                            p.terminate()
                            time.sleep(3)
                except psutil.NoSuchProcess, e:
                    pass


    def _performConcurrentOps(self, injectFailure, opFunc):
        threadList = []
        for threadId in range(self.numThreads):
            threadList.append(threading.Thread(target=opFunc))

        for thrd in threadList:
            thrd.start()

        # Inject failures, after some initial delay.
        if injectFailure:
            injectFailureThread = threading.Thread(target=self._injectFailure)
            injectFailureThread.start()

        for thrd in threadList:
            thrd.join()

        if injectFailure:
            self.injectFailureSignal.set()
            injectFailureThread.join()


    def setUp(self):
        self._init()

        # Start the monit daemon
        retCode = os.system("/usr/bin/monit")
        self.assertEqual(retCode, 0)
 
        # Start the blobstore service.
        retCode = os.system("/usr/bin/monit -g blobstore start")
        self.assertEqual(retCode, 0)


    def tearDown(self):

        # Stop the blobstore service.
        retCode = os.system("/usr/bin/monit -g blobstore stop")
        self.assertEqual(retCode, 0)
        # Stop monit daemon.
        retCode = os.system("/usr/bin/monit quit")
        self.assertEqual(retCode, 0)

        # Wait for some time before executing the next test.
        time.sleep(5)


    def testConcurrentWrites(self, injectFailure = False):
        # Initialize the counter
        self._initCounter()

        self._performConcurrentOps(injectFailure = injectFailure,
				   opFunc = self._incrementCounter)
        
        # Get the final count
        retCode, retVal = get(self.counterKey)
        self.assertEqual(retCode, 200)
        self.assertEqual(int(retVal), self.numThreads * self.iterCount)
  
        # Delete the counter
        self._removeCounter()


    def testConcurrentWritesWithFailures(self):
        self.testConcurrentWrites(injectFailure = True)


    def testBulkTransfer(self, injectFailure = False):
        self._performConcurrentOps(injectFailure = injectFailure,
				   opFunc = self._dispatchLargeBlobs)

        self.assertEqual(self.largeBlobCounter, self.numThreads * \
                                                self.iterCount)
        self._FetchAndDeleteLargeBlobs()


    def testBulkTransferWithFailures(self):
        self.testBulkTransfer(injectFailure = True)


    def testErrorRequests(self):
        # Generate a larger than allowed request.
        data = ''.join(choice(ascii_uppercase) for i in range(self.maxBlobSize + 1))
        reqId = self._generateRandomNumber()
        retCode, retVal = post(self.largeBlobKey.format(reqId), data)
        self.assertEqual(retCode, 413)

        # Generate a duplicate blob
        data = ''.join(choice(ascii_uppercase) for i in range(self.maxBlobSize))
        reqId = self._generateRandomNumber()
        retCode, retVal = post(self.largeBlobKey.format(reqId), data)
        self.assertEqual(retCode, 200)
        retCode, retVal = post(self.largeBlobKey.format(reqId), data)
        print retCode, retVal
        self.assertEqual(retCode, 403)
        retCode, retVal = delete(self.largeBlobKey.format(reqId))
        self.assertEqual(retCode, 200)
        
        # Blob doesnt exist. 
        reqId = self._generateRandomNumber()
        retCode, retVal = delete(self.largeBlobKey.format(reqId))
        self.assertEqual(retCode, 404)

        retCode, retVal = get(self.largeBlobKey.format(reqId))
        self.assertEqual(retCode, 404)

        data = ''.join(choice(ascii_uppercase) for i in range(self.maxBlobSize))
        retCode, retVal = put(self.largeBlobKey.format(reqId), data)
        self.assertEqual(retCode, 404)


if __name__ == '__main__':
    unittest.main()
