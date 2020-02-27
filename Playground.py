import glob
import os
import re
import shutil

import requests

def download_jpod_mp3(url: str, dest: str):
    filename = os.path.basename(url)
    downloadPath = dest + filename
    if not os.path.exists(downloadPath):
        r = requests.get(url, allow_redirects=True)
        open(downloadPath, 'wb').write(r.content)
