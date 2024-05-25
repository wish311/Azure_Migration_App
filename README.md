# Azure Migration and User/Guest Creation Tool

This Python application provides two main functionalities:
1. Azure Tenant Migration Tool
2. User/Guest Creation Tool

The application allows for tenant-to-tenant migration, user and guest account creation, and group management within Microsoft Azure using Microsoft Graph API and Azure Active Directory. The application features a modern GUI with light and dark modes.

## Features

### Azure Tenant Migration Tool
- Authenticate source and destination Azure tenants.
- Fetch and display groups from the destination tenant.
- Migrate users from the source to the destination tenant.
- Option to delete users from the source tenant after migration.

### User/Guest Creation Tool
- Authenticate Azure tenant.
- Fetch and display groups from the tenant.
- Create users based on SolarWinds Service Desk tickets.
- Create guests and add them to selected groups.
- Send email notifications with account details.

## Installation

### Prerequisites
- Python 3.8+
- Microsoft Azure Subscription
- Azure Active Directory
- SolarWinds Service Desk API credentials

### Install Dependencies
```bash
pip install -r requirements.txt
