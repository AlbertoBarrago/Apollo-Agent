"""
Publish the package to PyPI.
"""
import os

#Clean folder
os.system("rm -rf dist")
#Make build
os.system("python -m build .")
#Publish on PyPI
os.system("twine publish dist/*")
