# 🚀 Production Deployment Guide

**THE ONLY GUIDE YOU NEED TO FOLLOW**

## Quick Start (3 Steps)

1. **Configure environment**: `cp .env.example .env` (edit with your values)
2. **Validate setup**: `./pre_deploy_check.sh`
3. **Deploy**: `./deploy_production.sh`

That's it! The script handles everything automatically.

## Step-by-Step Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx certbot python3-certbot-nginx git
```

### 2. Database Setup

```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
CREATE DATABASE whatsapp_business;
CREATE USER 'whatsapp_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON whatsapp_business.* TO 'whatsapp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Application Setup

```bash
# Clone repository
git clone <your-repo-url> /var/www/whatsapp-business
cd /var/www/whatsapp-business

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your configuration
```

### 4. Environment Configuration

Edit `.env` file with your production values:

```bash
# Database
DB_HOST=localhost
DB_USER=whatsapp_user
DB_PASSWORD=your_secure_password
DB_NAME=whatsapp_business

# Security
SECRET_KEY=your-super-secure-secret-key-here

# Meta/WhatsApp API
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_REDIRECT_URI=https://yourdomain.com/onboard/callback

# Platform WhatsApp Business API
PLATFORM_WABA_ID=your_platform_waba_id
PLATFORM_PHONE_NUMBER_ID=your_platform_phone_id
PLATFORM_ACCESS_TOKEN=your_platform_access_token

# Payment Gateway
RAZORPAY_KEY_ID=rzp_live_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret

# Email
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-app-password
```

### 5. Run Deployment Script

```bash
# Make script executable
chmod +x deploy_production.sh

# Run deployment
./deploy_production.sh
```

### 6. SSL Certificate Setup

```bash
# Update domain in Nginx config
sudo nano /etc/nginx/sites-available/whatsapp-business

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 7. Final Configuration

1. **Update Meta redirect URI** in your Meta app settings
2. **Test the application**: `curl -I https://yourdomain.com`
3. **Monitor logs**: `sudo journalctl -u whatsapp-business -f`

## Post-Deployment

### Monitoring

```bash
# Check service status
sudo systemctl status whatsapp-business

# View logs
sudo journalctl -u whatsapp-business -f

# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Run health check
python3 health_check.py

# JSON output for monitoring
python3 health_check.py --json
```

### Backup

```bash
# Database backup
mysqldump -u whatsapp_user -p whatsapp_business > backup_$(date +%Y%m%d_%H%M%S).sql

# Application backup
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/whatsapp-business
```

### Updates

```bash
# Pull latest code
cd /var/www/whatsapp-business
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart whatsapp-business
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u whatsapp-business -n 50
   ```

2. **Database connection issues**
   ```bash
   mysql -u whatsapp_user -p whatsapp_business
   ```

3. **Nginx configuration errors**
   ```bash
   sudo nginx -t
   ```

4. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

### Performance Tuning

1. **Adjust Gunicorn workers** in systemd service file
2. **Configure MySQL** for your server specs
3. **Set up log rotation** (already included in deployment script)
4. **Monitor resource usage** with htop/top

## Security Checklist

- [ ] Strong database passwords
- [ ] Secure secret key
- [ ] SSL certificate installed
- [ ] Firewall configured (UFW recommended)
- [ ] Regular security updates
- [ ] Log monitoring setup
- [ ] Backup strategy implemented

## Support

For issues or questions:
1. Check logs first
2. Review this deployment guide
3. Check the troubleshooting section
4. Contact your development team