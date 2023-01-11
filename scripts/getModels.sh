#!/bin/bash

# Check if wget is installed
if ! [ -x "$(command -v wget)" ]; then
  # Install wget
  brew install wget
fi

# Set the URL of the file to download
url="https://github.com/ayoolaolafenwa/PixelLib/releases/download/0.2.0/pointrend_resnet50.pkl"

# Check if the "models" directory exists in "resources"
if [ ! -d "../resources/models" ]; then
  # Create the "models" directory in "resources"
  mkdir -p "../resources/models"
fi

# Set the destination directory and file
destination="../resources/models/pointrend_resnet50.pkl"

# Download the file using wget and specify the destination directory and file
wget $url -O $destination
