#!/usr/bin/env python
import web

urls = (
    '/store/blobs', 'all_blobs',
    '/store/(.*)', 'blob_store'
)

app = web.application(urls, globals())

class all_blobs:
    def GET(self):
        return "all_blobs" + "\n"

class blob_store:
    def GET(self, blob_location):
        return blob_location + "\n"

if __name__ == "__main__":
    app.run()
