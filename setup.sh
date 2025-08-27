#!/bin/bash

# Make sure we have the latest pip
pip install --upgrade pip

# Install the core scientific stack first to ensure binary compatibility
# Using specific stable versions for Python 3.11
pip install numpy==1.26.4 scipy==1.11.4 scikit-learn==1.3.2

# Now, install the rest of the libraries from requirements.txt
# This ensures they build against the stable foundation we just installed
pip install -r requirements.txt