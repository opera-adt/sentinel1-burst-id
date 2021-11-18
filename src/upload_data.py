"""Python S3 Manager"""

import sys
import os
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import json
from shapely.geometry import box
import requests


class s3UploadDownload:
    """
    A class to upload/pull files to/from S3.
    """

    def __init__(self, bucket_name=None):
        """
        constructor of the class. 
        """
        session = boto3.Session(
           aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.client = session.client('s3')
        self.resource = session.resource('s3')
        self.bucket_name = bucket_name

    def pull_file(self, file_name):
        """
        The function to download a file on the S3 bucket to the local instance.
        Parameters:
            file_name: name of the file on S3 bucket to pull.
        """

        self.check_bucket_exists()
        try:
            self.client.download_file(self.bucket_name, file_name, file_name)
        except ClientError:
            return False
        return True

    def put_file(self, file_name, object_name=None):
        """
            The function to upload a file to the S3 bucket.
            Parameters:
                file_name: name and path of the file to upload

        """

        if object_name is None:
            object_name = file_name
        self.check_bucket_exists()
        try:
            self.client.upload_file(file_name, self.bucket_name, object_name)
        except ClientError:
            return False
        return True



