# 🤖 AliExpress Multi-Channel Telegram Bot

Advanced multi-channel bot that automatically posts trending AliExpress products to 6+ Telegram channels with smart filtering, duplicate detection, and an interactive control panel.

## ✨ Features

- 🎛️ **Interactive Control Panel** - Manage all channels from Telegram with inline buttons
- 📺 **6 Pre-configured Channels** - Hot Deals, Tech, Home, Beauty, Under $10, Under $5
- 🎯 **Smart Filtering** - Price range, commission rate, keywords, exclude words
- 🚫 **Duplicate Detection** - Never post the same product twice
- 💰 **Real Discount Filter** - Only posts products with genuine discounts
- 🔗 **URL Shortening** - Clean TinyURL links
- ⏱️ **Dynamic Scheduling** - Each channel has its own posting interval
- 📊 **Live Statistics** - Track posted products and channel status
- 🎨 **Beautiful Messages** - Rich formatting with emojis and product details

## 📋 Prerequisites

1. **Python 3.10+** installed
2. **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
3. **6 Telegram Channels** (or create them as needed)
4. **AliExpress Affiliate Account** with API credentials
5. **VPS with Static IP** (required for AliExpress API whitelist)
   - Recommended: Contabo VPS S ($3.99/mo) or AWS EC2 Free Tier

## 🚀 Quick Start (Local Testing)

### Step 1: Clone Repository

```bash
git clone https://github.com/mohasbks/AliExpress-Bot.git
cd AliExpress-Bot
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALIEXPRESS_APP_KEY=your_app_key
ALIEXPRESS_APP_SECRET=your_app_secret
ALIEXPRESS_TRACKING_ID=your_tracking_id
ADMIN_USER_IDS=123456789,987654321
```

### Step 4: Run the Bot

```bash
python final_bot.py
```

### Step 5: Use Control Panel

Send `/start` to your bot on Telegram to access the interactive control panel!

---

## 🌐 VPS Deployment (Production)

### Why You Need a VPS

AliExpress API requires a **static IP address** in their whitelist. Cloud platforms like Railway/Heroku have dynamic IPs and won't work.

### Recommended VPS Providers

| Provider | Price/mo | Static IP | Best For |
|----------|----------|-----------|----------|
| **Contabo VPS S** | $3.99 | ✅ Free | Best value |
| **AWS EC2 t2.micro** | Free 12mo | ✅ Free | First year |
| **DigitalOcean** | $6 | ✅ Free | Easy setup |
| **Vultr** | $6 | ✅ Free | Fast speeds |

### VPS Deployment Steps

#### Option A: Using Environment Variables (Recommended)

**Windows (Command Prompt):**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHANNEL_ID=@your_channel_name
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHANNEL_ID="@your_channel_name"
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHANNEL_ID="@your_channel_name"
```

#### Option B: Edit the Script Directly

Open `aliexpress_telegram_bot.py` and modify these lines:

```python
TELEGRAM_BOT_TOKEN = "YOUR_ACTUAL_BOT_TOKEN"
TELEGRAM_CHANNEL_ID = "@your_actual_channel"
```

### Step 5: Run the Bot

```bash
python aliexpress_telegram_bot.py
```

The bot will:
1. Start immediately and post 1-3 products
2. Continue posting products every 2 hours automatically
3. Run until you stop it (Ctrl+C)

## Configuration Options

### Change Posting Frequency

Edit the scheduler interval in `aliexpress_telegram_bot.py`:

```python
# Post every 2 hours (default)
scheduler.add_job(post_products_job, 'interval', hours=2)

# Post every 4 hours
scheduler.add_job(post_products_job, 'interval', hours=4)

# Post every 30 minutes
scheduler.add_job(post_products_job, 'interval', minutes=30)
```

### Change Number of Products Posted

Modify this line in the `post_products_job()` function:

```python
# Post 1-3 random products (default)
num_products_to_post = random.randint(1, min(3, len(products)))

# Post exactly 5 products
num_products_to_post = 5

# Post 2-5 random products
num_products_to_post = random.randint(2, min(5, len(products)))
```

### Filter by Category

Add category filtering when fetching products:

```python
# Popular category IDs:
# 3 - Electronics
# 1501 - Phones & Accessories
# 7 - Computer & Office
# 66 - Women's Clothing

products = aliexpress.get_hot_products(
    category_ids="3,1501",  # Electronics and Phones
    page_size=20
)
```

## File Structure

```
happybir/
├── aliexpress_telegram_bot.py  # Main bot script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## How It Works

1. **Scheduler**: APScheduler runs the `post_products_job()` function every 2 hours
2. **API Call**: Fetches hot products from AliExpress Affiliates API
3. **Random Selection**: Selects 1-3 random products to avoid spam
4. **Formatting**: Creates attractive messages with product details
5. **Posting**: Sends product image and info to your Telegram channel
6. **Repeat**: Waits 2 hours and repeats

## Product Message Format

Each post includes:
- 📸 Product image
- 🛍️ Product title
- 💰 Current price (USD)
- 🏷️ Original price (if discounted)
- 🔥 Discount percentage
- 📦 Number of orders
- ⭐ Product rating
- 🛒 Direct link button to AliExpress

## Troubleshooting

### "Please set TELEGRAM_BOT_TOKEN environment variable!"

**Solution**: Set the `TELEGRAM_BOT_TOKEN` environment variable or edit the script directly.

### "Unauthorized" or "Bot was blocked by the user"

**Solution**: Make sure your bot is added as an administrator to the channel.

### "Chat not found"

**Solution**: 
- Use channel username with @ (e.g., `@mychannel`)
- Or use the numeric chat ID (e.g., `-1001234567890`)
- Make sure the bot is an admin of the channel

### "No products fetched from AliExpress"

**Solution**: 
- Check your internet connection
- Verify AliExpress API credentials are correct
- The API might be rate-limited; wait a few minutes

### Rate Limiting

The bot includes a 2-second delay between posts to avoid Telegram rate limits. If you post too many products too quickly, adjust the delay:

```python
time.sleep(5)  # Increase delay to 5 seconds
```

## Running as a Background Service

### Windows (using Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "When computer starts")
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\Users\PC\Desktop\happybir\aliexpress_telegram_bot.py`

### Linux (using systemd)

Create `/etc/systemd/system/aliexpress-bot.service`:

```ini
[Unit]
Description=AliExpress Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/happybir
Environment="TELEGRAM_BOT_TOKEN=your_token"
Environment="TELEGRAM_CHANNEL_ID=@your_channel"
ExecStart=/usr/bin/python3 aliexpress_telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable aliexpress-bot
sudo systemctl start aliexpress-bot
```

## API Documentation

- [AliExpress Affiliates API](https://developers.aliexpress.com/en/doc.htm)
- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

## Security Notes

- ⚠️ **Never commit your bot token to version control**
- ⚠️ Use environment variables for sensitive data
- ⚠️ Keep your API credentials secure

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review AliExpress API documentation
3. Check Telegram Bot API status

---

**Happy posting! 🚀**
