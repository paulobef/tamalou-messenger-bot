import os

import dropbox
import fasttext.util
from setuptools import setup, find_packages

from flaskr.utils.dropbox_connector import DropboxConnector

setup(name='tamalou_messenger_bot', version='1.0', packages=find_packages())

if not os.path.isdir('ml_models'):
    # get proprietary models from dropbox location
    dbx_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    dbx_app_folder_path = '/'
    dbx = dropbox.Dropbox(dbx_token)
    dbx_connector = DropboxConnector(dbx_app_folder_path, dbx)
    dbx_connector.download_folder('ml_models', './ml_models.zip')
    print('downloaded proprietary models')

# get fast text model from fast text website
fasttext.util.download_model('fr', if_exists='ignore')
print('downloaded fasttext model')

# make space by deleting zip files
if os.path.isfile('cc.fr.300.bin.gz'):
    os.remove('cc.fr.300.bin.gz')
if os.path.isfile('ml_models.zip'):
    os.remove('ml_models.zip')
print('deleted model archives')