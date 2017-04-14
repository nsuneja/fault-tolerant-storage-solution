DESCRIPTION:

This service provides a fault tolerant single node key value store, with
a REST base interface for performing CRUD operations on the blobstore.

The solution instantiates a group of processes, one out of which binds to
the port 7777, and opens up the blobstore for business. Also, this process
group is instantiated under monit's umbrella to ensure that a process which
dies, gets reborn.

So, when a process dies, 2 things happen:

1) One of the other processes in the process group binds itself to the port
and keeps the blobstore available. This is an analogy of a distributed file
system, where we elect a new leader (using some leader election receipe)
when the old leader dies.

2) Monit restarts the process in its process group which died, and that process
now starts polling for the ownership of port 7777.


================================================================

REQUIREMENTS:

1) python >= 2.7
2) python-pip (Python package manager)
3) Flask (Python web framework)
4) SQLAlchemy (SQL Toolkit and Object Relational Mapper)
5) monit (Process monitoring)
6) requests (Python REST client library - TESTING ONLY)
7) psutil (Python utility to manage processes - TESTING ONLY) 

=================================================================

INSTALL:

1) cd $HOME/fault-tolerant-storage-solution
2) ./configure.sh

==================================================================

START:

1) cd $HOME/fault-tolerant-storage-solution
2) ./run.sh

==================================================================

STOP:

1) cd $HOME/fault-tolerant-storage-solution
2) ./stop.sh

===================================================================

TEST:

1) cd $HOME/fault-tolerant-storage-solution
2) ./tests/blobstore_test.py

====================================================================

NOTE:

1) You should be logged in as 'root' user. The reason I went ahead with
   'root' user was of my solution's dependency on 'monit' daemon. Monit
   executes as 'root' user. For the sake of installation and execution
   simplicity, I decided to use the 'root' user. Although, with some
   changes in the installation and execution workflow, it should be easy
   enough to get around it.

2) The solution directory (fault-tolerant-storage-solution) should be placed
   under the $HOME directory.
