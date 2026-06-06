import os
from datetime import datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from google.cloud import storage
from mongoengine.errors import DoesNotExist, InvalidQueryError, FieldDoesNotExist

from ..schemas.profile_schema import UpdateProfileSchema
from ...schemas.general_schema import DataErrorSchema, DataSuccessSchema
from ..models.user_model import User
from ...helpers.default_data_updater import sync_user_data_status


class ProfileService:
    """Profile service"""

    def profile_info(self, user_id):
        """Get profil info"""
        try:
            user = User.objects(id=user_id).first()
            data = {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "picture": user.picture,
                "address": user.address,
                "is_there_data": user.is_there_data,
                "role_user": user.role_user,
            }
        except DoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200, message="Successfully to get the profile", payload=data
        )

    def update_profile(self, user_id, data: UpdateProfileSchema, file=None):
        """Update profile function"""
        try:
            if file:
                folder_name = os.getenv("GS_PROFILE_FOLDER_NAME")
                filename = (
                    f"{folder_name}/{str(datetime.now().timestamp())}-{file.name}"
                )
                default_storage.save(filename, ContentFile(file.read()))

                self.set_file_to_public(filename)
                image_url = self.get_file_info(filename)

                User.objects(id=user_id).update(
                    set__name=data.name,
                    set__phone=data.phone,
                    set__address=data.address,
                    set__picture=image_url,
                )
            else:
                User.objects(id=user_id).update(
                    set__name=data.name,
                    set__phone=data.phone,
                    set__address=data.address,
                )

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200, message="Successfully to update your profile", payload={}
        )

    def is_there_data_status(self, user_id):
        """generate status existing data"""
        try:
            data = {"is_there_data": sync_user_data_status(user_id)}
        except DoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except InvalidQueryError as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        except FieldDoesNotExist as exception:
            return 400, DataErrorSchema(code=400, message=str(exception))

        return 200, DataSuccessSchema(
            code=200, message="Successfully to profile status", payload=data
        )

    @staticmethod
    def get_file_info(file_path):
        """get file info"""
        # Create a client to interact with the Google Cloud Storage API
        client = storage.Client()

        # Get the bucket where the file is stored
        bucket = client.get_bucket(os.getenv("GS_BUCKET_NAME"))

        # Get the blob object representing the file
        # file_path = 'path/to/file.txt'
        blob = bucket.blob(file_path)

        # Get the public URL of the file
        public_url = blob.public_url

        return public_url

    @staticmethod
    def set_file_to_public(filename):
        """set file to public"""
        client = storage.Client()

        # Get the bucket where the file was saved
        bucket = client.get_bucket(os.getenv("GS_BUCKET_NAME"))

        # Get the blob object representing the file
        blob = bucket.blob(filename)

        # Make the file publicly accessible
        blob.make_public()
