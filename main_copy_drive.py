# -*- coding: utf-8 -*-
"""
Created on Sat Jan  9 17:34:01 2021

@author: Franz Richter

This script shows the simple set up of the class. The variable origin holds
the location where you want to copy all folders and files from. The variable
destination holds the location where you want to copy all those folders
and files to. 

"""
from drive_communicator import drive_communicator

#Folder that you want copied
origin = "Long string from the drive" 

#Location where you want to copy
destination = "another long string from thedrive" 

class_handle = drive_communicator(origin, destination)
class_handle.execution_copying()

