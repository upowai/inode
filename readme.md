# iNode Server Documentation

## Distributed Data Training

iNode Server is a Python-based application designed to manage and process jobs in a distributed network. It integrates with MongoDB, Redis, and external APIs to handle job assignments, validator updates, and miner management. The server also features a FastAPI web server for handling HTTP requests.

### iNode Flow

![iNode](https://raw.githubusercontent.com/upowai/inode/main/img/iNode.png)

## Prerequisites

Before setting up the iNode Server, ensure you have the following installed:

- Python 3.8 or higher
- MongoDB
- Redis (See the "Installing Redis" section below for installation instructions)
- Required Python libraries (listed in `requirements.txt`)

## Installing Redis

To ensure Redis is installed and properly configured on your system, you can use the `install_redis.sh` script. Follow these steps for your operating system:

### macOS and Ubuntu

1. **Make the Script Executable:**

   - Open a terminal and navigate to the directory containing the `install_redis.sh` script.
   - Run the command `chmod +x install_redis.sh` to make the script executable.

2. **Run the Script:**
   - Execute the script by running `./install_redis.sh` in the terminal.
   - If necessary, the script will ask for your password to grant permission for installation steps that require superuser access.

The script will check if Redis is already installed on your system and proceed with the installation if it is not. It also ensures that Redis is set to start on boot.

## Installing Mongodb

To Install Mongodb on Ubuntu you can use the `install_mongodb.sh` script.

### Ubuntu

1. **Make the Script Executable:**

   - Open a terminal and navigate to the directory containing the `install_mongodb.sh` script.
   - Run the command `chmod +x install_mongodb.sh` to make the script executable.

2. **Run the Script:**
   - Execute the script by running `./install_mongodb.sh` in the terminal.
   - If necessary, the script will ask for your password to grant permission for installation steps that require superuser access.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/upowai/inode.git
   ```

2. **Navigate to the Project Directory:**

   ```bash
   cd inode
   ```

3. **Install Dependencies:**

   ```bash
   pip3 install -r requirements.txt
   ```

4. **Configure MongoDB and Redis:**

   - Ensure MongoDB and Redis are running on your system.
   - Update the MongoDB connection URL and database details in `database/mongodb.py` if necessary.

5. **Set Up Environment Variables:**

   - Optionally, set up environment variables for configuration parameters.

6. **Generate SHA Keys:**

   - First, you need to generate a pair of SHA keys (public and private). Run the following command in your terminal:
     ```bash
     python generatekey.py
     ```
   - This script will generate two keys: a public key and a private key. You will use these keys for secure communication.
   - After generating the SHA keys, you need to set up your environment variables. Specifically, you will set up the private key of your registered Inode wallet.
   - Set from which block height you want iNode to start tracking rewards given by dobby emission (TRACKBLOCK).
   - Open `.env` file in your project root directory you can use command `nano .env`
   - Add the following lines to your `.env` file,`PRIVATEKEY=YOUR_INODE_WALLET_PRIVATEKEY` you check envExample for reference
     ```
     SHA_PRIVATEKEY=YOUR_SHA_PRIVATE_KEY
     SHA_PUBLICKEY=YOUR_SHA_PUBLIC_KEY
     PRIVATEKEY=YOUR_INODE_WALLET_PRIVATEKEY
     INODEWALLETADDRESS=YOUR_WALLET_ADDRESS
     INODEREWARDWALLETADDRESS=YOUR_ADDRESS_FOR_REWARD
     TRACKBLOCK=10000
     ```

7. **Prepare Your Development Environment**

   Depending on your operating system, you may need to install additional tools to ensure the `fastecdsa` Python package and other dependencies compile correctly:

   - **Ubuntu Users:**

     Install the necessary libraries by running:

     ```bash
     sudo apt-get update
     sudo apt-get install libgmp3-dev
     sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
     ```

   - **Windows Users:**

     Install Visual Studio, which includes the necessary C++ build tools. Download it from [https://visualstudio.microsoft.com/vs/preview/](https://visualstudio.microsoft.com/vs/preview/) and ensure to select the C++ workload during installation.
     [wikihow Install Clang on Windows](https://www.wikihow.com/Install-Clang-on-Windows)

   - **macOS Users:**

     Install Xcode or the standalone Command Line Tools for Xcode, which include `clang`. This can be done by installing Xcode from the Mac App Store or by running the following command in the terminal:

     ```bash
     xcode-select --install
     ```

     For users who prefer not to install Xcode, downloading Command Line Tools for Xcode from [Apple Developer Downloads](https://developer.apple.com/download/more/) is an alternative.
     [https://ics.uci.edu/~pattis/common/handouts/macclion/clang.html](https://ics.uci.edu/~pattis/common/handouts/macclion/clang.html)

   Please ensure these tools are correctly installed and configured on your system before proceeding with the installation of the Python package dependencies.

## Running the Server

1. **Start the iNode Server:**

   - Run the following command in the project directory:
     ```bash
     python3 inode.py
     ```
   - This will start the FastAPI server and the socket-based server for handling client connections.

2. **Accessing the API:**
   - The FastAPI server will be accessible at `http://localhost:8000`.
   - You can access the FastAPI configurations by navigating to `./utils/config.py`.

## Key Components

- **FastAPI Server:** Handles HTTP requests and provides an interface for job management and validator updates.
- **Socket Server:** Manages real-time connections with clients for job processing and data updates.
- **MongoDB Integration:** Stores and manages job and validator data.
- **Redis Integration:** Utilizes Redis for caching and managing real-time data.

## Features

- **Job Processing:** Assigns and tracks jobs to different nodes in the network.
- **Validator Management:** Updates and maintains validator data.
- **Miner Management:** Manages miner data and periodically updates the miner list.
- **Periodic Updates:** Regularly updates validator and miner data based on predefined intervals.

## API Endpoints

- **Validators Router:** Handles requests related to validators.
- **Jobs Management:** Endpoints for creating, updating, and tracking jobs.

## Troubleshooting

- Ensure MongoDB and Redis services are running before starting the server.
- Check the console logs for any errors or warnings.
- Validate the configuration settings in `inode.py` and `utils.py`.
