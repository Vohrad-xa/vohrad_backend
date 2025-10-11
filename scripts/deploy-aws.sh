#!/bin/bash
set -e

echo "Deploying Vohrad Backend to AWS EC2..."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DOMAIN=""
CERTBOT_EMAIL=""
DB_PASSWORD=""
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            CERTBOT_EMAIL="$2"
            shift 2
            ;;
        --db-password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --aws-access-key)
            AWS_ACCESS_KEY_ID="$2"
            shift 2
            ;;
        --aws-secret-key)
            AWS_SECRET_ACCESS_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option $1"
            echo "Usage: $0 --domain yourdomain.com --email admin@yourdomain.com --db-password strongpassword --aws-access-key KEY --aws-secret-key SECRET"
            exit 1
            ;;
    esac
done

if [ -z "$DOMAIN" ] || [ -z "$CERTBOT_EMAIL" ] || [ -z "$DB_PASSWORD" ] || [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}Missing required parameters${NC}"
    echo "Usage: $0 --domain yourdomain.com --email admin@yourdomain.com --db-password strongpassword --aws-access-key KEY --aws-secret-key SECRET"
    exit 1
fi

echo "Deployment Configuration:"
echo "  Domain: $DOMAIN"
echo "  Email: $CERTBOT_EMAIL"
echo "  Database Password: [HIDDEN]"

# Update system
echo ""
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
echo ""
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo ""
    echo "Installing Git..."
    sudo apt install -y git
fi

# Clone or update repository
if [ -d "/opt/vohrad" ]; then
    echo ""
    echo "Updating existing repository..."
    cd /opt/vohrad
    git pull
else
    echo ""
    echo "Cloning repository..."
    echo "NOTE: Repository is private. Make sure you have SSH deploy key configured."
    echo "If git clone fails, run these commands first:"
    echo "  ssh-keygen -t ed25519 -C 'vohrad-ec2-deploy' -f ~/.ssh/vohrad_deploy_key -N ''"
    echo "  cat ~/.ssh/vohrad_deploy_key.pub"
    echo "Then add the key to GitHub: https://github.com/Vohrad-xa/vohrad_backend/settings/keys"
    echo ""
    
    # Check if deploy key exists
    if [ ! -f ~/.ssh/vohrad_deploy_key ]; then
        echo -e "${RED}ERROR: SSH deploy key not found at ~/.ssh/vohrad_deploy_key${NC}"
        echo "Please set up the deploy key first (see instructions above)"
        exit 1
    fi
    
    # Ensure SSH config is set up
    if ! grep -q "github.com" ~/.ssh/config 2>/dev/null; then
        mkdir -p ~/.ssh
        cat >> ~/.ssh/config << 'SSHEOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/vohrad_deploy_key
    IdentitiesOnly yes
SSHEOF
        chmod 600 ~/.ssh/config
    fi
    
    sudo mkdir -p /opt/vohrad
    sudo chown -R $USER:$USER /opt/vohrad
    git clone git@github.com:Vohrad-xa/vohrad_backend.git /opt/vohrad
    cd /opt/vohrad
fi

# Set permissions
sudo chown -R $USER:$USER /opt/vohrad

# Create production environment file
echo ""
echo "Creating production environment..."
cat > .env.production << EOF
# Production environment configuration
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Database Configuration
DB_USER=postgres
DB_NAME=vohrad_prod
DB_PASS=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432

# Security (you should generate these properly)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# JWT Configuration
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=keys/jwt_private.pem
JWT_PUBLIC_KEY_PATH=keys/jwt_public.pem
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
WEB_COOKIE_MAX_AGE_SECONDS=21600

# CORS - Allow all origins for testing (TODO: Restrict in production!)
CORS_ALLOW_ORIGINS=["*"]

# Domain configuration
DOMAIN=$DOMAIN
CERTBOT_EMAIL=$CERTBOT_EMAIL

# AWS Credentials for Route 53 (for wildcard SSL)
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=eu-west-1

# PostgreSQL container variables
POSTGRES_USER=postgres
POSTGRES_DB=vohrad_prod
POSTGRES_PASSWORD=$DB_PASSWORD
PGPASSWORD=$DB_PASSWORD

# Other configurations...
STRIPE_SECRET_KEY=sk_live_YOUR_STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET
STRIPE_CURRENCY=eur
STRIPE_DAYS_UNTIL_DUE=7

RESEND_API_KEY=re_YOUR_RESEND_API_KEY
EMAIL_FROM_ADDRESS=noreply@$DOMAIN
EMAIL_FROM_NAME=Vohrad

LICENSE_RENEW_URL_TEMPLATE=https://$DOMAIN/renew-license?license_key={license_key}

# Logging
LOG_FILE_PATH=logs/app.log
LOG_ERROR_FILE_PATH=logs/error.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5
ENABLE_ECS_FIELDS=true
STRUCTURED_LOGS=true

PYTHONPATH=src
EOF

# Create SSL configuration for this domain
echo ""
echo "Setting up wildcard SSL configuration for $DOMAIN and *.$DOMAIN..."
# Process the production.conf template with the actual domain
envsubst '${DOMAIN}' < nginx/conf.d/production.conf > nginx/conf.d/default.conf

# Create required directories
mkdir -p logs backups certbot/conf certbot/www keys

# Generate JWT keys
echo ""
echo "Generating JWT keys..."
openssl genrsa -out keys/jwt_private.pem 2048
openssl rsa -in keys/jwt_private.pem -pubout -out keys/jwt_public.pem
chmod 600 keys/jwt_private.pem
chmod 644 keys/jwt_public.pem
echo "JWT keys generated successfully"

# Set up firewall
echo ""
echo "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Build and start services (without SSL first)
echo ""
echo "Building containers..."
docker compose --env-file .env.production -f docker-compose.prod.yml build

echo ""
echo "Starting services..."
docker compose --env-file .env.production -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 15

# Get wildcard SSL certificate
echo ""
echo "Obtaining wildcard SSL certificate for $DOMAIN and *.$DOMAIN..."
docker compose --env-file .env.production -f docker-compose.prod.yml --profile ssl-setup up certbot

# Restart nginx with SSL
echo ""
echo "Restarting nginx with SSL..."
docker compose --env-file .env.production -f docker-compose.prod.yml restart nginx

# Set up cron job for certificate renewal
echo ""
echo "Setting up SSL certificate renewal (runs every Monday at 3 AM)..."
(crontab -l 2>/dev/null; echo "0 3 * * 1 cd /opt/vohrad && docker compose --env-file .env.production -f docker-compose.prod.yml --profile ssl-setup up certbot && docker compose --env-file .env.production -f docker-compose.prod.yml restart nginx") | crontab -

# Set up daily backups
echo ""
echo "Setting up daily database backups (runs daily at 2 AM)..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/vohrad && docker compose --env-file .env.production -f docker-compose.prod.yml --profile backup up backup") | crontab -

echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo "Your application is available at:"
echo -e "  HTTPS: ${GREEN}https://$DOMAIN${NC}"
echo -e "  API Docs: ${GREEN}https://$DOMAIN/docs${NC}"

echo ""
echo "Next steps:"
echo "  1. Create admin user: docker compose --env-file .env.production -f docker-compose.prod.yml exec api pdm run python management/manage.py user create-with-role"
echo "  2. Create tenant: docker compose --env-file .env.production -f docker-compose.prod.yml exec api pdm run python management/manage.py tenant create_tenant"
echo "  3. Update your Stripe/Email API keys in .env.production"

echo ""
echo "Useful commands:"
echo -e "  View logs: ${YELLOW}docker compose --env-file .env.production -f docker-compose.prod.yml logs -f${NC}"
echo -e "  Check status: ${YELLOW}docker compose --env-file .env.production -f docker-compose.prod.yml ps${NC}"
echo -e "  Restart: ${YELLOW}docker compose --env-file .env.production -f docker-compose.prod.yml restart${NC}"