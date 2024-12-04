# HostHub - Cultural Exchange Platform

HostHub is a web platform designed to facilitate cultural exchange by connecting travelers with hosts who offer accommodation in exchange for volunteer work. The platform primarily targets the Chinese travel market, providing a structured way for meaningful cultural exchanges.

## Features

- **User Authentication**
  - Secure registration and login system
  - Role-based access (Host/Traveler)
  - Profile management

- **For Hosts**
  - Create and manage work exchange listings
  - View and respond to traveler applications
  - Track listing status and history

- **For Travelers**
  - Search listings by location
  - View detailed listing information
  - Submit and track applications

## Technology Stack

- **Backend**
  - Python 3.11
  - Flask web framework
  - MySQL database
  - Flask-Login for authentication
  - Flask-WTF for forms

- **Frontend**
  - HTML5/CSS
  - Bootstrap for responsive design
  - JavaScript for interactive features

## Installation

1. Clone the repository:
git clone https://github.com/xiaodangaoooo/HostHub.git
cd HostHub

Create and activate a virtual environment:

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

Install required packages:

pip install -r requirements.txt

Create a .env file in the project root with the following content:

SECRET_KEY=your_secret_key
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DB=hosthub

Initialize the database:

flask init-db
Running the Application

Make sure your virtual environment is activated
Run the development server:

python run.py

Access the application at http://localhost:3000