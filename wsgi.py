import os
from app import app

UPLOAD_FOLDER = '/data'
BASE_URL = os.environ.get('BASE_URL', 'https://dl.cinvu.net/')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if __name__ == "__main__":
    app.run()



