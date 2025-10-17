# Security Guidelines

## Environment Variables and Secrets Management

This application uses environment variables for configuration, including sensitive data like database passwords. Follow these best practices to keep your deployment secure.

### Environment Variables

The application uses the following environment variables:

- `DB_PASSWORD` - Database password (default: `DbServer123`, **should be changed for production**)

### Optional Environment Variables

These have safe defaults but can be customized:

- `DB_USER` - Database username (default: `etl_user`)
- `DB_NAME` - Database name (default: `stcp_warehouse`)
- `DB_HOST` - Database host (default: `127.0.0.1`)
- `DB_PORT` - Database port (default: `5432`)

## Best Practices

### 1. Never Commit Secrets

- **Never** commit passwords, API keys, or other secrets to version control
- The `.gitignore` file is configured to exclude `.env` files
- Always use environment variables for sensitive configuration

### 2. Setting Environment Variables

For Docker Deployment:
```bash
# Set the required password
export DB_PASSWORD='your_secure_password_here'

# Optional: customize other settings
export DB_USER='custom_user'
export DB_NAME='custom_database'

# Run the deployment
./docker/deploy.sh
```

### 3. Production Deployments

For production environments:

1. **Change the default password**: The application uses a default password (`DbServer123`) for quick setup, but this should be changed for security
   ```bash
   # Generate a strong password for production
   openssl rand -base64 32
   ```

2. **Restrict access**: Use firewall rules to limit database access

3. **Use secrets management**: Consider using tools like:
   - Docker Secrets (for Docker Swarm)
   - Kubernetes Secrets (for K8s deployments)
   - AWS Secrets Manager / Azure Key Vault (for cloud deployments)
   - HashiCorp Vault (for enterprise environments)

4. **Regular updates**: Keep dependencies and Docker images up to date

5. **Monitor logs**: Review application and database logs regularly

### 4. Docker-Specific Security

- Database data is persisted in Docker volumes (survives container restarts)
- Containers communicate via internal Docker network (not exposed to host)
- Only necessary ports are exposed (80 for web, 8000 for API)
- PostgreSQL port (5432) is NOT exposed to the host by default

## Reporting Security Issues

If you discover a security vulnerability, please report it by:

1. Opening a GitHub issue with the `security` label
2. Providing details about the vulnerability
3. Suggesting a fix if possible

Do not publicly disclose the vulnerability until it has been addressed.

## Security Checklist

Before deploying to production:

- [ ] Database password is changed from default via `DB_PASSWORD`
- [ ] `.env` files (if any) are in `.gitignore`
- [ ] No secrets are committed to version control
- [ ] Database access is restricted by firewall
- [ ] SSL/TLS is configured for web access (if applicable)
- [ ] Regular backups are configured
- [ ] Monitoring and logging are enabled
- [ ] Dependencies are up to date

## Additional Resources

- [Installation Guide (Traditional)](../README.md) - Complete traditional installation with detailed system setup
- [Docker Installation Guide](../docker/README.md) - Docker deployment instructions
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [PostgreSQL Security Best Practices](https://www.postgresql.org/docs/current/security.html)
- [Twelve-Factor App](https://12factor.net/) - Configuration best practices
