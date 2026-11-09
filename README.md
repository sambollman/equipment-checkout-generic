# Key & Equipment Checkout System

RFID-based self-service checkout system for tracking keys and equipment. Staff scan their keycard and equipment fob - the system tracks who has what, when, and where.

## Features

- Real-time Tracking: See which items are checked out and who has them
- RFID-Based: Fast checkout using employee keycards and equipment fobs
- Self-Registering: New employees and items register automatically on first scan
- Checkout: Scan one card, then scan one or more items and tap Done
- Vendor Checkout: Staff check out key-box fobs on behalf of a vendor; the vendor's name is recorded once per checkout and shown on the dashboard, in checkout history, and in the CSV export
- Card/Fob Replacement: Replace lost or damaged keycards and fobs
- Notes System: Add warnings or reminders with optional expiration dates
- Live Dashboard: Updates in real-time via WebSockets
- Admin Panel: Web-based management for users, equipment, and checkout history
- Categories: Keys, Rentables, Tools, Vehicles, Lock Box, Cleaning, Signs (customizable)
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

The kiosk shows a logo on its main screen if `riverrock_logo.png` is in the same folder as `kiosk_gui.py` (download it from this repo along with kiosk_gui.py). It is a white logo on a transparent background, sized for the kiosk's black screen. If the file is missing, the kiosk falls back to a key icon.

## Kiosk Main Screen

The main screen is kept simple for day-to-day use:

- Checkout
- Vendor Checkout
- Stock Parts Out
- Stock Parts In
- Cut Key
- More: opens a second page with Add Note, Add New, Reserve, Edit/Cancel Reservation, and Back. The More page returns to the main screen after 60 seconds of inactivity.

Replacing a lost or broken equipment fob or employee fob is done from the admin panel, not the kiosk.

On the dashboard, checked-out items are listed first in the Keys, Rentables, and Tools tabs.

## Kiosk Controls

- ESC: Reset to welcome screen
- F11: Enter fullscreen
- F12: Exit fullscreen

## Vendor Checkout

When a vendor is taking a key from the key box:

1. Tap Vendor Checkout on the kiosk main screen
2. Scan your own keycard
3. Scan each key-box fob the vendor is taking
4. Tap Done and enter the vendor's name once (required; it applies to every fob in that checkout)

The items are recorded under the staff member's name with the vendor name attached (the checkouts.vendor_name column, added automatically on startup). Scanning a fob the regular way from the main screen does not ask for a vendor, so staff must tap Vendor Checkout first. Items are checked back in by scanning them as usual.

### Several vendors, same property (Keys)

Keys fobs can be held by more than one person at once, so two vendors can each take the key for the same property drawer. A regular or Vendor Checkout of a Keys fob that is already out simply adds another holder. The dashboard shows one card per fob listing every holder. When a fob with more than one holder is scanned to return it, the kiosk asks who is returning (tap a name, or Return all); a fob with a single holder checks in immediately. Other categories keep the old behavior (a second checkout is a handoff).

## Customizing Categories

Categories are defined in several places. To add or rename one, update all of them:

- kiosk_gui.py: the `categories = [...]` list used when registering a new item (search for `categories =`). If items in the category need a property address at checkout, also add it to `PROPERTY_NOTE_CATEGORIES`.
- app.py: `PROPERTY_NOTE_REQUIRED_CATEGORIES` (same property-address rule on the server), and the category grouping used to build the dashboard (search for `'Cleaning'`).
- templates/admin.html and templates/edit_fob.html: the category dropdowns.
- templates/index.html: a tab button and a card section for the new category. Without these, items in the new category appear only on the All tab.

Current categories: Keys, Rentables, Tools, Vehicles, Lock Box, Cleaning, Signs, plus Discontinued and Other.

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
