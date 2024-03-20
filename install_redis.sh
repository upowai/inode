#!/bin/bash

# Function to check if Redis is installed
is_redis_installed() {
    if command -v redis-server &> /dev/null; then
        echo "Redis is already installed."
        return 0
    else
        echo "Redis is not installed."
        return 1
    fi
}

# Function to install Redis on macOS
install_redis_macos() {
    echo "Installing Redis on macOS..."
    # Check if Redis is already installed
    if is_redis_installed; then
        echo "Skipping installation."
        return
    fi
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Install Redis using Homebrew
    brew update
    brew install redis
    # Start Redis service and ensure it starts on boot
    brew services start redis
    echo "Redis installation completed on macOS."
}

# Function to install Redis on Ubuntu
install_redis_ubuntu() {
    echo "Installing Redis on Ubuntu..."
    # Check if Redis is already installed
    if is_redis_installed; then
        echo "Skipping installation."
        return
    fi
    # Update package lists
    sudo apt-get update
    # Install Redis
    sudo apt-get install redis-server -y
    # Enable Redis to start on boot
    sudo systemctl enable redis-server.service
    # Start Redis service
    sudo systemctl start redis-server.service
    echo "Redis installation completed on Ubuntu."
}

# Detect the operating system
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    *)          OS="UNKNOWN:${OS}"
esac

# Install Redis based on the detected OS
if [ "${OS}" = "Linux" ]; then
    # Assuming Ubuntu or Ubuntu-based system
    install_redis_ubuntu
elif [ "${OS}" = "Mac" ]; then
    install_redis_macos
else
    echo "Unsupported operating system: ${OS}"
    exit 1
fi
