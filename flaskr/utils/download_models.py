import os
import fasttext.util


def download_models(dbx_connector):
    if not os.path.isdir('ml_models'):
        # get proprietary models from dropbox location
        dbx_connector.download_folder('ml_models', './ml_models.zip')
        print('downloaded proprietary models')

    # get fast text model from fast text website
    fasttext.util.download_model('fr', if_exists='ignore')
    print('downloaded fasttext model')

    # make space by deleting zip files
    if os.path.isfile('cc.fr.300.bin.gz'):
        os.remove('cc.fr.300.bin.gz')
        print('deleted fasttext model archives')
    if os.path.isfile('ml_models.zip'):
        os.remove('ml_models.zip')
        print('deleted proprietary model archives')