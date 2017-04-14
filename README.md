DESCRIPTION:

This service provides a fault tolerant single node key value store, with
a REST base interface for performing CRUD operations on the blobstore.


REQUIREMENTS:

1) python >= 2.7
2) python-pip (Python package manager)
3) Flask (Python web framework)
4) SQLAlchemy (SQL Toolkit and Object Relational Mapper)
5) monit (Process monitoring)
6) requests (Python REST client library - TESTING ONLY)
7) psutil (Python utility to manage processes - TESTING ONLY) 

INSTALL:

1) Execute configure.sh (It can be executed from ay directory)

START:

1) Execute run.sh. (It can be executed from any directory)

STOP:

1) Execute stop.sh. (It can be executed from any directory)

NOTE:

1) You should be logged in as 'root' user. The reason I went ahead with
   'root' user was of my solution's dependency on 'monit' daemon. Monit
   executes as 'root' user. For the sake of installation and execution
   simplicity, I decided to use the 'root' user. Although, with some
   changes in the installation and execution workflow, it should be easy
   enough to get around it.

2) The solution directory (fault-tolerant-storage-solution) should be placed
   under the $HOME directory.
