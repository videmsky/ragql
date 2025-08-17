"""A Python Pulumi program"""
import os
import pulumi
# run the following command to install the Neon provider:
#$ pulumi package add terraform-provider kislerdm/neon
import pulumi_neon as neon

config = pulumi.Config()
api_key = os.environ.get('NEON_API_KEY') or config.require_secret("api_key")
name = config.get('name') or 'yourname'

neon_provider = neon.Provider(f"{name}-neon-provider",
    api_key=api_key)

project = neon.Project(f"{name}-neon-project",
    name=name,
    region_id="aws-us-west-2",
    history_retention_seconds=21600,
    opts=pulumi.ResourceOptions(provider=neon_provider))

# NEON_CONNECTION_STRING=postgresql://username:password@hostname/database?sslmode=require
pulumi.export('NEON_CONNECTION_STRING', project.connection_uri)

# run the following command to see the connection string:
#$ pulumi stack output NEON_CONNECTION_STRING --show-secrets