### **📄 README.md**
```md
# Website Scraper with Selenium


Crawl a website for all related webpages
Webscrape all WebPages


---

## 🔧 Setup Instructions

### 1️⃣ Install Python (if not already installed)
Ensure you have **Python 3.7+** installed.  
Check by running:
```bash
python --version
```
or
```bash
python3 --version
```

If Python is not installed, download it from: [python.org](https://www.python.org/downloads/).

---

### 2️⃣ Create a Virtual Environment
Run the following command to create and activate a virtual environment:

#### 📌 **On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### 📌 **On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️⃣ Install Dependencies
After activating the virtual environment, install the required Python packages:

```bash
pip install -r requirements.txt
```

**`requirements.txt` file:**
```txt
selenium
```

---

### 4️⃣ Download ChromeDriver
- **Check your Chrome version** by opening `chrome://settings/help` in Chrome.
- Download the matching **ChromeDriver** from: [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/)
- Extract and place it in the project folder.
- Update the `CHROMEDRIVER_PATH` in `scraper.py` to match the file location.

---

### 5️⃣ Add URLs to `urls.json`
Create a JSON file called `urls.json` in the project folder with the list of pages to scrape:

```json
[
    "https://example.com",
    "https://example.com/page2"
]
```

---

### 6️⃣ Run the Script
Execute the script using:

```bash
python scraper.py
```

---

## 🛑 Deactivating the Virtual Environment
After running the script, deactivate the virtual environment:

```bash
deactivate
```

(On Windows, use `venv\Scripts\deactivate` instead.)

---

## 🚀 Features
✅ Uses **Selenium** to render JavaScript-powered pages.  
✅ Saves full **HTML** content.  
✅ Reads URLs from a **JSON file**.  
✅ Stores files in a **designated folder**.  
✅ **Runs in headless mode** for efficiency.  

---

### 🔥 Need More?
Feel free to modify and improve this scraper! 🚀
```

---

### **How to Use This**
- Save this as `README.md` in your project.
- Create a `requirements.txt` file and include `selenium`.
- Follow the steps in the **README** to set up your environment and run the scraper.