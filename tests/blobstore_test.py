#!/usr/bin/python
import unittest
import threading
import requests
import os
import time

restEndpointURL = "http://127.0.0.1:7777/store/"

def post(key, value):
    response = requests.post(restEndpointURL + key, data = value)
    return response.status_code, response.text

def get(key):
    response = requests.get(restEndpointURL + key)
    return response.status_code, response.text

def put(key, value):
    response = requests.put(restEndpointURL + key, data = value)
    return response.status_code, response.text

def delete(key):
    response = requests.delete(restEndpointURL + key)
    return response.status_code, response.text


class ConcurrentWriteTest(unittest.TestCase):

    def _initConstants(self):
        self.counterKey = "counterKey2"
        self.counterInitVal = 0
        self.numThreads = 10
        self.iterCount = 100
        self.readModifyWriteLock = threading.Lock()

    
    def _initCounter(self):
        retCode, retVal = post(self.counterKey, str(self.counterInitVal))
        self.assertEqual(retCode, 200)


    def _removeCounter(self):
        retCode, retVal = delete(self.counterKey)
        self.assertEqual(retCode, 200)


    def _incrementCounter(self):
        for i in range(self.iterCount):
            with self.readModifyWriteLock:
                retCode, retVal = get(self.counterKey)
                self.assertEqual(retCode, 200)
                counter = int(retVal)
                counter += 1
                retCode, retVal = put(self.counterKey, str(counter))
                self.assertEqual(retCode, 200)
            time.sleep(0.1) 


    def setUp(self):
        self._initConstants()

        # Start the monit daemon
        retCode = os.system("sudo /usr/bin/monit")
        self.assertEqual(retCode, 0)
 
        # Start the blobstore service.
        retCode = os.system("sudo /usr/bin/monit -g blobstore start")
        self.assertEqual(retCode, 0)

        # Initialize the counter
        self._initCounter() 


    def tearDown(self):

        # Delete the counter
        self._removeCounter()

        # Stop the blobstore service.
        retCode = os.system("sudo /usr/bin/monit -g blobstore stop")
        self.assertEqual(retCode, 0)
        # Stop monit daemon.
        retCode = os.system("sudo /usr/bin/monit quit")
        self.assertEqual(retCode, 0)


    def testConcurrentWrites(self):
        threadList = []
        for threadId in range(self.numThreads):
            threadList.append(threading.Thread(target=self._incrementCounter))

        for thrd in threadList:
            thrd.start()

        for thrd in threadList:
            thrd.join()

        # Get the final count
        retCode, retVal = get(self.counterKey)
        self.assertEqual(retCode, 200)
        self.assertEqual(int(retVal), self.numThreads * self.iterCount)


if __name__ == '__main__':
    unittest.main()
