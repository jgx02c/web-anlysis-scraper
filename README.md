### **📄 README.md**
```md
# Steps to Obtain SEO Data for Each Website and All Pages

## 1. Start with the Main URL
- Begin with the main URL of the website's home page.

## 2. Prepare for Crawling
- Delete any existing `urls.json`.
- Add the main URL to the `crawler.py` script.

## 3. Run the Crawler
- Execute `crawler.py`.
- Review the output in `urls.json`:
  - Clean any outliers and duplicates (e.g., `instagram.com`, `facebook.com`).
  - Manually `Cmd + Click` on links in the JSON to verify webpage validity.

## 4. Prepare for Scraping
- Delete any existing folder named `downloaded_pages` to prevent contamination.

## 5. Run the Scraper
- Execute `scraper.py`.
- Review the output in the `downloaded_pages` folder:
  - Open each file in a web browser to confirm validity.

## 6. Prepare for Cleaning
- Delete any existing folder named `cleaned_pages` to prevent contamination.

## 7. Run the Cleaner
- Execute `cleaner_v2.py`.
- Review the output in the `cleaned_pages` folder:
  - Open each file in a web browser to confirm validity.

## 8. Upload to Vectorstore
- Run `upsert_pages.py` to upload the cleaned pages to the vectorstore.

## 9. Validate the Upload
- Run `rag_service.py` to verify that the new pages are successfully uploaded.

---

## Create Vector DB ##
- Run `rag_embeddings.py` to create the vectorDB and upsert all cleaned pages to the vectorstore.

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

## 🛑 Deactivating the Virtual Environment
After running the script, deactivate the virtual environment:

```bash
deactivate
```

(On Windows, use `venv\Scripts\deactivate` instead.)

---


## Nessary Scripts ##

crawler.py              # Gets all Url's associated with Main URL
scraper.py              # Uses the Url's to scrape for the HTML content
cleaner.py              # Clean up the HTML, moving to .txt after Scraping
rag_upsert.py           # Adds Documents to the VectorDB 
chunker.py              # Chunks the text during Upserting
rag_service.py          # Query's the VectorDB

rag_embeddings.py       # Create the vectorstore and DB **Only Use if DB not created**
rag_remove.py           # Remove the documents from the VectorDB