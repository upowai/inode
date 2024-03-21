#!/bin/bash

# Check if MongoDB is already installed by checking for mongod command
if mongod --version &> /dev/null; then
    echo "MongoDB is already installed."
    exit 0
fi

# Install necessary packages
sudo apt install software-properties-common gnupg apt-transport-https ca-certificates -y

# Add the MongoDB GPG key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add the MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update your package list
sudo apt update

# Install MongoDB
sudo apt install mongodb-org -y

# Start and enable MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Optionally, check MongoDB service status
# sudo systemctl status mongod --no-pager

echo "MongoDB installation and setup completed."
# Display MongoDB version
mongod --version
