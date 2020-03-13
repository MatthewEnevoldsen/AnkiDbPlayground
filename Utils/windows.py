import xml.etree.ElementTree as ET
import re
import pandas as pd
import os
import requests
import csv
from joblib import Parallel, delayed

def __init__():
    pass

def downloadFile(url: str, dest: str):
    if not os.path.exists(dest):
        r = requests.get(url, allow_redirects=True)
        open(dest, 'wb').write(r.content)
