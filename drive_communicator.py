# -*- coding: utf-8 -*-
"""
Created on Fri Feb  5 14:07:08 2021

@author: Franz Richter

This class will connect to the drive. It then will copy the content
of one drive (ID given by user) to another drive location (ID also given)


"""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
from googleapiclient.http import MediaIoBaseDownload
import numpy as np


class drive_communicator:
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination
        self.listoffiles = []
        self.maporigintodestinationids = {}

    def execution_copying(self):
        self.initialise_link_to_drive()

        'Get all Folders in folders '
        folder_id = self.origin
        self.recursion_folder(folder_id)
        return self.listoffiles

    def initialise_link_to_drive(self):
        """
        Here we will get the Link to all drives and permission

        """
        SCOPES = ['https://www.googleapis.com/auth/drive']
        ' Get Login data'
        creds = self.getcreds(SCOPES)
        ' Loads our link to software '
        self.drive_service = build('drive', 'v3', credentials=creds)

    def getcreds(self, SCOPES):
        ' Function to give you access to your drive'
        creds = None
        # The file token.pickle stores the user's access and refresh tokens,
        # and is created automatically when the authorization flow
        # completes for the first time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def recursion_folder(self, folder_id):
        'Loops through all the folder to open the file '
        folderlist = self.foldersinfolder(folder_id)

        if not folderlist:
            self.copyfilesinfolder(folder_id)
        else:
            for f in folderlist:
                self.createfolderindestination(f["name"], f["id"], folder_id)
                self.recursion_folder(f['id'])
                self.copyfilesinfolder(folder_id)

    def foldersinfolder(self, folder_id):
        "List all Folders in one Folder"
        query = "mimeType='application/vnd.google-apps.folder' and parents in '{}' and trashed = false".format(folder_id)
        page_token = None
        folderlist = []
        while True:
            response = self.drive_service.files().list(q=query,
                                                       fields='nextPageToken, files(id, name)',
                                                       pageToken=page_token,
                                                       ).execute()
            folderlist.extend(response['files'])
            'Break if None pageToken'
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return folderlist

    def copyfilesinfolder(self, folder_id):
        file_list_origin = self.listfilesinfolder(folder_id)

        "Get parent id at destination"
        parentfolder_id_destination = self.getparentid(folder_id)
        file_list_destination = self.listfilesinfolder(
                                parentfolder_id_destination)

        for file in file_list_origin:
            "lets copy the file if a file of the name does not already exist"
            existing_id = self.checkfilesinfilelist(file.get("name"),
                                                    file_list_destination)
            if not existing_id:
                file = self.drive_service.files().copy(fileId=file.get('id'),
                                                       body={"parents":
                                                             [parentfolder_id_destination]}
                                                       ).execute()

    def createfolderindestination(self, foldername_origin, folder_id_origin,
                                  parentfolder_id_origin):
        """
        We will use a dictonary to store the corresponding destination id and
        origin id.The key of the dict is the origin id, and the value
        is the destination id. If a value is not in the dictonary
        then it is getting assigned to the top level
        """
        parentfolder_id_destination = self.getparentid(parentfolder_id_origin)

        """
        Now we will check if folder already exists and if so we will get
        its idea
        """
        existing_id = self.checkfolderinfolderlist(foldername_origin,
                                                   parentfolder_id_destination)

        if existing_id:
            folder_id_destination = existing_id
        else:
            file_metadata = {
                "name": foldername_origin,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parentfolder_id_destination]
                }
            file = self.drive_service.files().create(body=file_metadata,
                                                     fields='id').execute()
            folder_id_destination = file.get("id")
        "Add to dictonary"
        self.maporigintodestinationids[folder_id_origin] = folder_id_destination

    def checkfolderinfolderlist(self, foldername, parentfolder_id_destination):
        folderlist = self.foldersinfolder(parentfolder_id_destination)
        if folderlist:
            for file in folderlist:
                name = file.get("name")
                if name == foldername:
                    return file.get("id")
        return []

    def getparentid(self, parentfolder_id_origin):
        if parentfolder_id_origin in self.maporigintodestinationids:
            parentfolder_id_destination = self.maporigintodestinationids[parentfolder_id_origin]
        else:
            parentfolder_id_destination = self.destination
        return parentfolder_id_destination

    def checkfilesinfilelist(self, file_name, file_list):
        if file_list:
            for file in file_list:
                name = file.get("name")
                if name == file_name:
                    return file.get("id")
        return []

    def listfilesinfolder(self, folder_id):
        query = "mimeType !='application/vnd.google-apps.folder' and parents in '{}' and trashed = false".format(folder_id)
        page_token = None
        results = []
        while True:
            response = self.drive_service.files().list(q=query,
                                                       fields='nextPageToken, files(id, name)',
                                                       pageToken=page_token
                                                       ).execute()
            results.extend(response["files"])
            'Break if None pageToken'
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return results

