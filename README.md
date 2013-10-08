gluster-deploy
--------------
The project is intended to provide admins with a simple to use UI, to bootstrap a glusterfs or Red Hat Storage installation. The goal is to remove the laborious tasks, and ensure that configuration steps are the same across all nodes in a cluster.

**Design Goal**  
The goal of the project is to produce something that has only depends on the standard python packages. The UI is web based, but just uses standard javascript/css3 techniques - so no jquery or web frameworks like django to worry about ;o)

**Status**  
Currently the 'wizard' implements the following;

 - Discover listening glusterd processes  
 - Form a cluster from the discovered nodes  
 - distribute local ssh keys to all nodes  
 - scan each node for unused disks  
 - gather information about the use case for gluster  
 - Apply the use case information to format and mount the bricks across all nodes

**Requirements**  
 - python >= 2.6  
 - openssh server and client on each gluster node

**Tested on**  
 - Red Hat Storage 2.1

**Installation Process**  
Install the script by unpacking the tar file in a suitable location on one of the intended nodes within the new cluster.

**Usage**  
Execute the script with

    ./gluster-deploy.py

To get an idea of the workflow provided by the UI, take a look at the screenshots folder.


> Written with [StackEdit](http://benweet.github.io/stackedit/).