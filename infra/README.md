# Ragql Infrastructure

This directory contains the Pulumi infrastructure code for provisioning a Neon PostgreSQL database for the Ragql project.

## Prerequisites

1. Install Pulumi CLI: https://www.pulumi.com/docs/install/
2. Install UV package manager: https://docs.astral.sh/uv/getting-started/installation/
3. Get a Neon API key: https://console.neon.tech/app/settings/api-keys

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set your Neon API key (choose one method):
   ```bash
   # Option 1: Environment variable
   export NEON_API_KEY="your-api-key-here"
   
   # Option 2: Pulumi config (encrypted)
   pulumi config set --secret ragql:api_key "your-api-key-here"
   ```

3. Configure your project name (optional, defaults to "yourname"):
   ```bash
   pulumi config set ragql:name "your-project-name"
   ```

## Usage

### Deploy Infrastructure
```bash
# Preview changes
pulumi preview

# Deploy the stack
pulumi up
```

### Get Database Connection String
```bash
# View the connection string (includes credentials)
pulumi stack output NEON_CONNECTION_STRING --show-secrets
```

### Update Infrastructure
```bash
# Make changes to __main__.py, then:
pulumi preview  # Review changes
pulumi up       # Apply changes
```

### Destroy Infrastructure
```bash
pulumi destroy
```

## Configuration

The infrastructure creates:
- A Neon PostgreSQL project in `aws-us-west-2` region
- 6-hour history retention
- Exports the connection string as `NEON_CONNECTION_STRING`

Modify `__main__.py` to customize the database configuration.