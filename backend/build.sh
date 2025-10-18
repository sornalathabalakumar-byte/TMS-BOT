#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install system dependencies for the MS ODBC Driver
apt-get update
apt-get install -y curl apt-transport-https gnupg

# 2. Add Microsoft's official package repository
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3. Update package list and install the driver, automatically accepting the EULA
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

# 4. Install Python dependencies
pip install -r requirements.txt
