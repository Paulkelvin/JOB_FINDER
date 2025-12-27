# 🌍 GeoJob-Sentinel

**Production-Grade CLI Application for Finding Niche GIS Specialist I/II and Analyst Roles**

A robust, 100% free-to-operate job finder that automatically discovers, filters, and notifies you about junior-to-mid level GIS positions from multiple sources.

---

## 🎯 Features

### Multi-Source Data Collection
- **Greenhouse/Lever APIs**: Query public job boards from top GIS companies
- **Google Dorking via Serper.dev**: Find hidden Workday postings from firms like AECOM, Jacobs, HDR
- **Smart Filtering**: Focus on Specialist I/II and Analyst roles only

### Intelligence Layer
- **Keyword Guard**: Only jobs with 'GIS', 'Geospatial', 'Spatial', or 'Mapping'
- **Seniority Filter**: Automatically excludes Senior, Lead, Manager, Director, etc.
- **SQLite Deduplication**: Never see the same job twice

### Notifications
- **Discord Rich Embeds**: Beautiful job alerts with direct links
- **Batch Processing**: Efficient multi-job notifications
- **Summary Reports**: Scan statistics after each run

### Reliability & Stealth
- **User-Agent Rotation**: Avoid detection with fake-useragent
- **Exponential Backoff**: Random 10-30s delays between requests
- **Comprehensive Error Handling**: Continues running even if sources fail
- **Production Logging**: Track everything for debugging

---

## 📋 Requirements

- **Python 3.8+**
- **Free API Keys**:
  - [Serper.dev](https://serper.dev) (2,500 free searches/month)
  - Discord Webhook URL (completely free)

---

## 🚀 Quick Start

### 1. Installation

```powershell
# Clone or download the repository
cd C:\Users\paulo\Documents\JOB_FINDER

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```powershell
# Copy the example config
copy config.example.yaml config.yaml

# Edit config.yaml with your details
notepad config.yaml
```

**Required Configuration:**

1. **Get Serper.dev API Key**:
   - Visit https://serper.dev
   - Sign up (free, no credit card)
   - Copy your API key
   - Paste into `config.yaml` under `serper.api_key`

2. **Create Discord Webhook**:
   - Open Discord → Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the Webhook URL
   - Paste into `config.yaml` under `discord.webhook_url`

3. **Add Target Companies**:
   - Edit the `ats.company_slugs` list
   - Find company slugs by visiting their careers page
   - Example: `https://boards.greenhouse.io/esri` → slug is `esri`

### 3. Run the Application

```powershell
# Basic run
python geojob_sentinel.py

# With verbose logging
python geojob_sentinel.py -v

# Show database statistics
python geojob_sentinel.py --stats

# Use custom config file
python geojob_sentinel.py -c my-config.yaml
```

---

## 🤖 Automation Setup

### Option A: GitHub Actions (Cloud - Recommended)

**Advantages**: Runs 24/7 in the cloud, completely free, no local computer needed

**Setup Steps**:

1. **Create GitHub Repository**:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit: GeoJob-Sentinel"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/geojob-sentinel.git
   git push -u origin main
   ```

2. **Add Secrets to GitHub**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add two secrets:
     - `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
     - `SERPER_API_KEY`: Your Serper.dev API key

3. **Enable Actions**:
   - Go to Actions tab
   - Enable workflows
   - The scanner will run every 6 hours automatically

4. **Manual Trigger**:
   - Actions → GeoJob-Sentinel Auto Scan → Run workflow

**Database Persistence**: GitHub Actions uses caching to maintain your SQLite database between runs.

---

### Option B: Windows Task Scheduler (Local)

**Advantages**: Full control, runs on your PC

**Setup Steps**:

1. **Create a batch script** (`run_scanner.bat`):
   ```batch
   @echo off
   cd /d C:\Users\paulo\Documents\JOB_FINDER
   python geojob_sentinel.py
   ```

2. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

3. **Create Basic Task**:
   - Action → Create Basic Task
   - Name: "GeoJob-Sentinel Scanner"
   - Trigger: Daily (or your preference)
   - Action: Start a program
   - Program: `C:\Users\paulo\Documents\JOB_FINDER\run_scanner.bat`

4. **Advanced Settings** (Optional):
   - Right-click task → Properties
   - Triggers → Edit → Advanced → Repeat task every: 6 hours
   - Duration: Indefinitely

---

## 📊 Usage Examples

### View Statistics
```powershell
python geojob_sentinel.py --stats
```

Output:
```
============================================================
DATABASE STATISTICS
============================================================
Total jobs tracked:     47
Jobs (last 7 days):     12

Jobs by source:
  Greenhouse: 23
  Serper/Google: 18
  Lever: 6
============================================================
```

### Customize Filters

Edit `config.yaml`:

```yaml
filters:
  required_keywords:
    - "gis"
    - "geospatial"
    - "cartography"  # Add custom keywords
  
  negative_keywords:
    - "senior"
    - "lead"
    - "consultant"  # Add custom exclusions
```

### Add More Companies

```yaml
ats:
  company_slugs:
    - "esri"
    - "planet"
    - "YOUR_TARGET_COMPANY"  # Add more slugs
```

**How to find company slugs**:
1. Visit company careers page
2. Look for Greenhouse: `https://boards.greenhouse.io/SLUG`
3. Or Lever: `https://jobs.lever.co/SLUG`

---

## 🔧 Configuration Reference

### Full `config.yaml` Structure

```yaml
database:
  path: "geojob_sentinel.db"  # Database file location

discord:
  webhook_url: "YOUR_WEBHOOK_URL"  # Discord webhook for notifications

serper:
  api_key: "YOUR_API_KEY"  # Serper.dev API key
  custom_dorks:  # Custom Google search queries
    - 'site:myworkdayjobs.com "GIS" -senior'

ats:
  company_slugs:  # List of company slugs to scan
    - "esri"
    - "mapbox"

filters:
  required_keywords:  # Job title must contain at least one
    - "gis"
    - "geospatial"
  
  negative_keywords:  # Exclude jobs containing any of these
    - "senior"
    - "manager"

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "geojob_sentinel.log"
```

---

## 📁 Project Structure

```
JOB_FINDER/
├── geojob_sentinel.py      # Main application
├── database.py             # SQLite deduplication
├── ats_fetcher.py          # Greenhouse/Lever scraper
├── serper_fetcher.py       # Google dork via Serper.dev
├── job_filter.py           # Keyword filtering logic
├── discord_notifier.py     # Discord webhook integration
├── config.yaml             # Your configuration (gitignored)
├── config.example.yaml     # Template configuration
├── requirements.txt        # Python dependencies
├── geojob_sentinel.db      # SQLite database (auto-created)
├── geojob_sentinel.log     # Application logs
├── .github/
│   └── workflows/
│       └── job-scanner.yml # GitHub Actions workflow
└── README.md              # This file
```

---

## 🎨 Discord Notification Format

Each job notification appears as a rich embed:

```
╔══════════════════════════════════════╗
║ 🎯 GIS Analyst I                    ║
║ 🏢 Company: Esri                    ║
║ 📍 Location: Remote                 ║
║ 🔍 Source: Greenhouse               ║
║                                      ║
║ [Apply Now →]                        ║
╚══════════════════════════════════════╝
```

Summary notifications include:
- New jobs found
- Total scanned
- Duplicates filtered
- Jobs by source breakdown

---

## 🛠️ Troubleshooting

### "Configuration file not found"
**Solution**: Copy `config.example.yaml` to `config.yaml` and fill in your details.

### "Error fetching from Serper API"
**Solutions**:
- Check your API key is correct
- Verify you haven't exceeded free tier (2,500 searches/month)
- Check internet connection

### "Error sending Discord notification"
**Solutions**:
- Verify webhook URL is correct
- Test webhook manually: `curl -X POST YOUR_WEBHOOK_URL -H "Content-Type: application/json" -d "{\"content\": \"Test\"}"`
- Check Discord server permissions

### No jobs found
**Solutions**:
- Check your filter keywords aren't too restrictive
- Verify company slugs are correct (visit their careers page)
- Enable verbose logging: `python geojob_sentinel.py -v`

### GitHub Actions not running
**Solutions**:
- Verify secrets are set correctly (Settings → Secrets)
- Check Actions tab for error messages
- Ensure repository is not private (or has Actions enabled)

---

## 🔒 Security Best Practices

1. **Never commit `config.yaml`**: Already in `.gitignore`
2. **Use GitHub Secrets**: For API keys in GitHub Actions
3. **Rotate API Keys**: Periodically regenerate your Serper.dev key
4. **Webhook Security**: Keep Discord webhook URLs private

---

## 📈 Performance & Limits

### Free Tier Limits
- **Serper.dev**: 2,500 searches/month (≈83/day or ≥3 scans/hour at 100 results each)
- **GitHub Actions**: 2,000 minutes/month (each run takes ~2-3 minutes)
- **Discord Webhooks**: Unlimited (rate limit: 30 requests/60 seconds)

### Recommended Scan Frequency
- **GitHub Actions**: Every 6 hours (4 scans/day)
- **Local Task Scheduler**: Every 4-8 hours
- **Manual**: As needed

### Resource Usage
- **CPU**: Minimal (mostly I/O bound)
- **Memory**: ~50MB
- **Disk**: ~1MB database (grows slowly)
- **Network**: ~1-5MB per scan

---

## 🧪 Testing

### Test Individual Components

```powershell
# Test database
python -c "from database import JobDatabase; db = JobDatabase(); print(db.get_stats())"

# Test filters
python -c "from job_filter import JobFilter; jf = JobFilter(); print(jf.is_valid_job({'title': 'GIS Analyst I'}))"

# Test Discord (replace with your webhook)
python -c "from discord_notifier import DiscordNotifier; dn = DiscordNotifier('YOUR_WEBHOOK'); dn.send_summary({'new_jobs': 5, 'total_scanned': 100})"
```

---

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and customize for your needs
- Report bugs via GitHub Issues
- Suggest improvements

---

## 📝 License

This project is provided as-is for personal use. Respect the terms of service of:
- Serper.dev API
- Discord webhooks
- Job board platforms (Greenhouse, Lever, Workday)

---

## 🎓 Learning Resources

### Understanding the Code
- **SQLite**: [Python SQLite Tutorial](https://docs.python.org/3/library/sqlite3.html)
- **APIs**: [Requests Documentation](https://requests.readthedocs.io/)
- **YAML**: [PyYAML Guide](https://pyyaml.org/wiki/PyYAMLDocumentation)

### GIS Career Resources
- [GIS Career Guide](https://www.gislounge.com/gis-career-guide/)
- [Esri Careers](https://www.esri.com/careers)
- [r/gis Community](https://reddit.com/r/gis)

---

## 💡 Tips & Tricks

### Maximize Results
1. **Research company slugs**: Check careers pages of top GIS firms
2. **Customize Google dorks**: Target specific metro areas or companies
3. **Adjust scan frequency**: More frequent = faster alerts, but uses quota

### Optimize Filters
1. **Review false positives**: Check logs for jobs that shouldn't pass
2. **Add negative keywords**: Exclude "consultant", "contractor", etc.
3. **Expand required keywords**: Add "cartography", "remote sensing"

### Stay Organized
1. **Create Discord channels**: Separate channels for different job types
2. **Use multiple configs**: Different configs for different job searches
3. **Regular cleanup**: Archive old database monthly

---

## 🆘 Support

**Issue**: Can't find company slugs?
**Answer**: Visit company's careers page, look for "greenhouse.io" or "lever.co" in URL.

**Issue**: Too many jobs?
**Answer**: Add more negative keywords or tighten required keywords.

**Issue**: Not enough jobs?
**Answer**: Add more company slugs, expand to Lever, use broader search dorks.

---

## 📅 Version History

- **v1.0.0** (2025-01-27): Initial release
  - Multi-source job fetching (ATS + Google)
  - Smart filtering and deduplication
  - Discord notifications
  - GitHub Actions support

---

## 🎯 Roadmap

Future enhancements:
- [ ] Email notifications (alongside Discord)
- [ ] Web dashboard for job tracking
- [ ] LinkedIn integration
- [ ] Resume auto-submit (with user approval)
- [ ] Salary range extraction
- [ ] Company rating integration (Glassdoor)

---

**Built with ❤️ for GIS professionals seeking their next opportunity.**

**Questions?** Review the troubleshooting section or check the logs at `geojob_sentinel.log`.

**Good luck with your job search! 🌍🗺️**
