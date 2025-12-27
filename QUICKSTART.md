# 🚀 GeoJob-Sentinel - Quick Start Guide

**Get up and running in 5 minutes!**

---

## Prerequisites

- Python 3.8 or higher installed
- Internet connection
- Discord account (for notifications)

---

## Step 1: Install Dependencies (1 minute)

Open PowerShell or Command Prompt in this folder and run:

```powershell
pip install -r requirements.txt
```

---

## Step 2: Get Your API Keys (2 minutes)

### A. Serper.dev API Key (FREE)

1. Visit https://serper.dev
2. Click "Sign Up" (no credit card required)
3. Verify your email
4. Copy your API key from the dashboard

### B. Discord Webhook URL (FREE)

1. Open Discord and go to your server
2. Right-click the channel where you want alerts
3. Edit Channel → Integrations → Webhooks
4. Click "New Webhook"
5. Copy the Webhook URL

---

## Step 3: Configure the App (2 minutes)

### Option A: Use Setup Wizard (Recommended)

```powershell
python setup_wizard.py
```

Follow the prompts to enter your API keys.

### Option B: Manual Configuration

1. Copy the example config:
   ```powershell
   copy config.example.yaml config.yaml
   ```

2. Edit `config.yaml` with Notepad:
   ```powershell
   notepad config.yaml
   ```

3. Replace these values:
   - `YOUR_DISCORD_WEBHOOK_URL_HERE` → Your Discord webhook URL
   - `YOUR_SERPER_API_KEY_HERE` → Your Serper.dev API key

4. Save and close

---

## Step 4: Run Your First Scan! (30 seconds)

### Windows:
```powershell
# Double-click run_scanner.bat
# OR run in terminal:
python geojob_sentinel.py
```

### Linux/Mac:
```bash
python3 geojob_sentinel.py
```

---

## What Happens Next?

The scanner will:
1. ✅ Query Greenhouse/Lever APIs for GIS companies
2. ✅ Search Google (via Serper) for Workday job postings
3. ✅ Filter out senior/manager roles
4. ✅ Check for duplicates in the database
5. ✅ Send new jobs to your Discord channel

**First run**: Expect 5-30 jobs depending on your config
**Subsequent runs**: Only new jobs will be sent

---

## View Results

### In Discord:
- Check the channel you configured
- Each job appears as a rich embed with a direct link

### In Terminal:
- Scan statistics are displayed
- Check `geojob_sentinel.log` for details

### View Database Stats:
```powershell
python geojob_sentinel.py --stats
```

---

## Automation Setup (Optional)

### Option 1: Windows Task Scheduler

1. Open Task Scheduler (`Win + R` → `taskschd.msc`)
2. Create Basic Task → "GeoJob-Sentinel"
3. Trigger: Daily at 9:00 AM
4. Action: Start Program → Browse to `run_scanner.bat`
5. Advanced: Repeat every 6 hours

### Option 2: GitHub Actions (Cloud)

1. Create a GitHub repository
2. Push your code (config.yaml is gitignored automatically)
3. Add secrets to repo:
   - Settings → Secrets → Actions
   - Add `DISCORD_WEBHOOK_URL` and `SERPER_API_KEY`
4. Enable Actions → Workflow runs automatically every 6 hours

**See README.md for detailed automation instructions**

---

## Troubleshooting

### "Config file not found"
**Fix**: Run `python setup_wizard.py` or copy `config.example.yaml` to `config.yaml`

### "No jobs found"
**Fix**: 
- First run may find nothing if jobs were already scraped
- Wait a few hours and run again
- Check logs: `type geojob_sentinel.log`

### "API Error"
**Fix**:
- Verify your Serper API key is correct
- Check you haven't exceeded 2,500 searches/month
- Test internet connection

### "Discord Error"
**Fix**:
- Verify webhook URL is correct (should start with `https://discord.com/api/webhooks/`)
- Check channel permissions

---

## Customization

### Add More Companies

Edit `config.yaml`:
```yaml
ats:
  company_slugs:
    - "esri"
    - "mapbox"
    - "YOUR_COMPANY"  # Add here
```

Find slugs: Visit `https://boards.greenhouse.io/COMPANY_NAME`

### Adjust Filters

```yaml
filters:
  required_keywords:
    - "gis"
    - "cartography"  # Add custom keywords
  
  negative_keywords:
    - "senior"
    - "contractor"  # Add custom exclusions
```

---

## Next Steps

1. ✅ **Test the scanner**: Run it a few times manually
2. ✅ **Set up automation**: Choose Task Scheduler or GitHub Actions
3. ✅ **Customize filters**: Add/remove keywords based on results
4. ✅ **Add companies**: Research and add more target companies
5. ✅ **Monitor Discord**: Check alerts and apply to jobs!

---

## Resources

- **Full Documentation**: See README.md
- **Troubleshooting**: README.md → Troubleshooting section
- **GitHub Actions Setup**: README.md → Automation Setup

---

## Support

**Need help?** Check:
1. `geojob_sentinel.log` for error details
2. README.md for comprehensive docs
3. Verify API keys and webhook URL

---

**You're all set! 🎉**

The scanner is now ready to find your next GIS opportunity automatically.

**Good luck with your job search! 🌍🗺️**
