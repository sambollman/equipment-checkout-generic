# Key & Equipment Checkout System

RFID-based self-service checkout system for tracking keys and equipment. Staff scan their keycard and equipment fob - the system tracks who has what, when, and where.

## Features

- Real-time Tracking: See which items are checked out and who has them
- RFID-Based: Fast checkout using employee keycards and equipment fobs
- Self-Registering: New employees and items register automatically on first scan
- Bulk Checkout: Scan one card, then scan multiple items
- Card/Fob Replacement: Replace lost or damaged keycards and fobs
- Notes System: Add warnings or reminders with optional expiration dates
- Live Dashboard: Updates in real-time via WebSockets
- Admin Panel: Web-based management for users, equipment, and checkout history
- Categories: Keys, Vehicles, Equipment, Tools, Other (customizable)
- Reservation System: Reserve items in advance
- Dashboard Password Protection: Secure the dashboard from public access

## Hardware Required

- Raspberry Pi (Pi 4 or Pi 5 recommended)
- RFID Card Reader: HID 5427CK Gen 2 (USB keyboard wedge style)
- RFID Keycards: 125kHz compatible cards for employees
- RFID Fobs: For equipment/keys you want to track
- Optional: TV/monitor for dashboard display

## Installation

Prerequisites: Docker (curl -sSL https://get.docker.com | sh) and Git (sudo apt install git)

    git clone https://github.com/sambollman/equipment-checkout-generic.git
    cd equipment-checkout-generic
    python3 database.py
    docker build -t checkout-system .
    docker run -d --name checkout-app --restart unless-stopped -p 5000:5000 \
      -v $(pwd):/data \
      -e DB_PATH=/data/key_checkout.db \
      -e KIOSK_USER=kiosk \
      -e KIOSK_PASS=your-kiosk-password \
      -e ADMIN_PASSWORD=your-admin-password \
      -e DASHBOARD_PASS=your-dashboard-password \
      -e SECRET_KEY=your-random-secret-key \
      checkout-system

Access at http://YOUR-SERVER-IP:5000

## Environment Variables

- KIOSK_USER / KIOSK_PASS: Credentials for kiosk API authentication
- ADMIN_PASSWORD: Password for admin panel at /admin/login
- DASHBOARD_PASS: Password for dashboard (leave empty to disable)
- SECRET_KEY: Random string for Flask session security
- DB_PATH: Path to SQLite database file

## Setting Up a Domain and SSL

### Option 1: Cloud Server (recommended)
Get a VPS (DigitalOcean, Linode, etc. ~$6/month), point your domain DNS to the server IP, install Docker and clone the repo, then set up nginx:

    sudo apt install nginx certbot python3-certbot-nginx

Create /etc/nginx/sites-available/checkout with this content:

    server {
        server_name yourdomain.com;
        location / {
            proxy_pass http://localhost:5000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

Then enable and get free SSL:

    sudo ln -s /etc/nginx/sites-available/checkout /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
    sudo certbot --nginx -d yourdomain.com

### Option 2: Raspberry Pi at your location
Set up port forwarding on your router (ports 80 and 443 to your Pi). Use DuckDNS (free) if you don't have a static IP. Then follow the nginx steps above.

Note: The proxy_set_header lines are required for WebSocket real-time updates to work.

## Kiosk Setup (Windows)

1. Install Python 3.12+ from python.org
2. Install dependencies: pip install requests pytz
3. Download kiosk_gui.py from this repo
4. Create Start_Kiosk.bat with these contents:

    @echo off
    cd C:\checkout-system
    set SERVER_URL=http://YOUR-SERVER-IP:5000
    set KIOSK_USER=kiosk
    set KIOSK_PASS=your-kiosk-password
    python kiosk_gui.py

5. Connect your RFID reader via USB and run Start_Kiosk.bat

## Kiosk Controls

- ESC: Reset to welcome screen
- F11: Enter fullscreen
- F12: Exit fullscreen

## Customizing Categories

Edit kiosk_gui.py around line 2130:
    categories = ["Keys", "Vehicles", "Equipment", "Tools", "Other"]

Also update the dropdowns in templates/edit_fob.html and templates/admin.html to match.

## Admin Panel

Access at http://YOUR-DOMAIN/admin/login

- View and manage all users and equipment
- View full checkout history
- Add notes with optional expiration dates
- Create reservations for specific items
- Replace lost cards or fobs
- Export data to CSV

## First Time Setup

1. Start the system and go to the admin panel
2. Add yourself as an admin user
3. At the kiosk, scan your keycard - it will prompt you to register
4. Scan an equipment fob - it will prompt you to register the item
5. Check the dashboard to confirm real-time updates are working

## Support

Open-source project. For issues visit https://github.com/sambollman/equipment-checkout-generic


