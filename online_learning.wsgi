




import sys
import os
from flask import Flask
from flask import render_template, redirect, url_for
from flask import request
import json
path=__file__[0:-20]
print("PATH: ",path)
sys.path.insert(0,path)


from app import app as application