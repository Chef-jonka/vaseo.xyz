# LLM Acceptably Report - Client Portal

A simple Flask web application for clients to securely view their AI bot traffic analysis reports.

## Features

- Secure login with bcrypt password hashing
- Client isolation (users can only see their own reports)
- Admin panel for managing clients
- Simple report delivery via HTML files
- Responsive, professional design
- Session-based authentication

## Quick Start

### 1. Install Dependencies

```bash
cd llm-acceptably-report
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python3 app.py
```

The server will start at: **http://localhost:5000**

### 3. Default Credentials

| User  | Username | Password  | Access Level |
|-------|----------|-----------|--------------|
| Demo  | demo     | demo123   | Client       |
| Admin | admin    | admin123  | Admin        |

## Directory Structure

```
llm-acceptably-report/
├── app.py                 # Flask application
├── database.db            # SQLite database (auto-created)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── reports/              # Client reports storage
│   └── [client-id]/      # Folder per client
│       └── report.html   # HTML report files
├── static/
│   └── css/
│       └── style.css     # Application styling
└── templates/
    ├── login.html        # Login page
    ├── dashboard.html    # Client dashboard
    └── admin.html        # Admin panel
```

## Adding Reports

1. Generate your AI bot traffic report as an HTML file
2. Navigate to the `reports/` folder
3. Find or create the client's folder (matching their **Client ID**)
4. Copy the HTML report file into that folder
5. The report will automatically appear in the client's dashboard

### Example

To add a report for client "acme-corp":

```bash
cp my-report.html reports/acme-corp/jan-2025.html
```

### Naming Convention

Use descriptive filenames:
- `jan-2025.html`
- `q1-2025-report.html`
- `2025-01-monthly.html`

Reports are sorted alphabetically (descending) in the dashboard.

## Adding New Clients

### Via Admin Panel (Recommended)

1. Log in as admin (`admin` / `admin123`)
2. Go to the Admin Panel
3. Fill in: Username, Password, Client ID
4. Click "Add Client"

The client's report folder is created automatically.

### Client ID Rules

- Letters, numbers, hyphens, and underscores only
- No spaces
- Used as the folder name in `reports/`

## Security Notes

- Passwords are hashed with bcrypt
- Sessions are managed securely by Flask
- Clients cannot access other clients' reports
- Path traversal attacks are prevented
- Change the `SECRET_KEY` in production!

## Production Deployment

For production use:

1. Set a secure secret key:
   ```bash
   export SECRET_KEY="your-very-secure-random-key"
   ```

2. Use a production WSGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. Set up HTTPS via reverse proxy (nginx/Apache)

4. Change default admin password immediately

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Redirect to dashboard/login |
| `/login` | GET/POST | Login page |
| `/logout` | GET | Logout and clear session |
| `/dashboard` | GET | Client dashboard (reports list) |
| `/view/<client>/<file>` | GET | View a report |
| `/download/<client>/<file>` | GET | Download a report |
| `/admin` | GET/POST | Admin panel |

## Troubleshooting

### "Module not found" errors

```bash
pip install Flask bcrypt
```

### Database issues

Delete `database.db` and restart the app to reinitialize.

### Permission errors on reports folder

```bash
chmod -R 755 reports/
```

## License

MIT License - Vaseo.xyz

## Support

For questions or issues, contact: vasilandreev199@gmail.com
