# Online registration and sign-in

The Account icon supports **Create account**, **Sign in** and **Sign out** on the included private calculation server. Accounts persist in SQLite on the host; passwords use salted PBKDF2-SHA256 with 600,000 iterations, and seven-day sessions use hashed random tokens and HttpOnly cookies. Account requests enforce same-origin JSON requests and attempt limits. Signing in or out starts a fresh calculation session. Accounts are optional: visitors can also calculate as guests. Registration does not verify ownership of an email address; password reset and email delivery are not implemented.

The standalone `index.html` cannot host an online account database. Its Account icon asks for the HTTPS address of your hosted software and opens that server. It never collects a password for an unconfigured server.

## HTTPS hosting with Docker Compose

Use a Linux server with Docker Compose, a domain pointing to the server, and inbound TCP ports 80 and 443 (UDP 443 is optional). From the `protected` folder:

```sh
KP_HOST=astrology.your-domain.example docker compose up -d --build
```

Replace the example hostname with your own real domain. Caddy obtains and renews HTTPS certificates. Only Caddy exposes network ports; Chromium and the calculation server run on the private container network. The `accounts` volume stores account records; preserve and back up this volume when upgrading. The software ZIP does not include account data. Do not publish the SQLite database or expose port 8080 directly. Set the same HTTPS address in the downloaded app's Account icon.

This host includes a single calculation worker and allows four active calculation sessions, which expire after 30 minutes of inactivity. Size and extend this worker pool before offering a larger public service. Account registration alone does not count as a calculation session.

## Run the server without Docker

Install Chromium and Noto fonts with your operating system's package manager, then:

```sh
python3 -m pip install -r protected/requirements.txt
python3 protected/server.py --port 8080
```

The default bind address is `127.0.0.1`. Use a reverse proxy with HTTPS for public hosting, set `KP_COOKIE_SECURE=1`, and set `KP_ACCOUNT_DATABASE` to a private persistent writable path. `CALCULATOR_CHROMIUM` can override `/usr/bin/chromium`. The `--host` option is available for a protected container network; the default remains loopback.

The server and account workflow are tested with Chromium and SQLite. A public domain and HTTPS deployment must be configured on your hosting server; no public account server address is bundled or claimed.

Validation in the development environment: hosted registration/sign-in/logout and native Chromium reports passed, and the Compose configuration validated. A container image build could not finish because the build container could not resolve the Debian package server; HTTPS certificate issuance and public deployment are to be verified on your host.
