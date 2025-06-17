#!/bin/bash
# Get the current working directory
current_directory=$(pwd)
cd src/
javac *.java
java VRPLoadingUnloadingMain $current_directory

exit

