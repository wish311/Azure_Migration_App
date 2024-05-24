# Azure Tenant Migration App

This app helps to migrate data between two Azure tenants with a user-friendly GUI.

## Requirements

- Python 3.x
- Azure Identity
- Azure Management Resource
- PyQt5

## Installation

1. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2. Install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the app:
    ```bash
    python main.py
    ```

2. Sign in to both Azure tenants.

3. Select the data types to migrate and click on "Migrate Data".
