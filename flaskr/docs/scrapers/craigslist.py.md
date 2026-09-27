Here is an itemized, object-oriented structural breakdown of flaskr/scrapers/craigslist.py.

### **Module: CraigslistScraperModule**

A specialized web scraper for Craigslist listings near Athens, TX (zip code 75751). It stores structured listing data in `craigslist_postings` and creates a linked blog post for the existing feed.

#### **Constants & Environment Setup**

* **root\_dir**: System path resolution dynamically locating and prepending the application root directory to sys.path.  
* **BASE\_URL**: Target Craigslist endpoint (\[https://easttexas.craigslist.org/search/sss\](https://easttexas.craigslist.org/search/sss)).

### **Service: CraigslistScraperEngine (get\_craigslist\_listings)**

Scrapes search results, parses listing metadata, and prepares a structured listing record plus formatted blog-post content.

#### **Parameters & Default State**

* **query**: Search string (Default: "surfboard").  
* **max\_results**: Maximum number of valid listings to return per run (Default: 5).

#### **Execution Pipeline & Filtering Business Logic**

> 1. **Target URL Construction**: Encodes the query string and appends geographic parameters (search\_distance=100\&postal=75751).  
> 2. **HTTP Request Generation**: Dispatches a GET request using custom User-Agent and Accept headers with a 10-second timeout.  
> 3. **HTML Parsing & Selection**: Processes DOM using BeautifulSoup matching selector candidates (.result-row, .cl-search-result, li.cl-static-search-result).  
> 4. **Filtering Rules**:  
   * **Keyword Filter**: Ignores any listing containing "modem" (case-insensitive) in the title.  
   * **Age Filter**: Ignores listings posted more than 24 hours prior to execution (now \- post\_time \> timedelta(days=1)).  
> 5. **URL Formatting**: Resolves relative listing URLs against the East Texas Craigslist search URL.  
> 6. **Unique-ID Deduplication**: Reads the Craigslist listing ID from the result row or listing URL and skips IDs already stored in SQLite before requesting detail pages. Duplicate IDs in the current search result batch are also skipped.  
> 7. **Detail Page Metadata Extraction**: Fetches image, description, location, and coordinates when available from the listing detail page.  
> 8. **Structured Payload Generation**: Returns the Craigslist ID, raw title and price, numeric price when parseable, location, coordinates, listing URL, category, search query, posting timestamp, image URL, and description, along with formatted blog-post content.

### **Service: ScrapedDataPersistenceService (insert\_scraped\_post)**

Database interface layer handling persistence of scraped items.

#### **Execution Flow & Database Constraints**

* **Context Creation**: Runs within the Flask application's database context.  
* **Database Deduplication**: Uses `INSERT OR IGNORE` and the unique `craigslist_id` constraint in `craigslist_postings`.  
* **Structured Listing Storage**: Persists listing identity and available price, location, category, query, timestamps, image, and description metadata.  
* **Blog Feed Projection**: Creates a linked `post` row with status `new` only when the Craigslist ID is new, then stores its ID in `craigslist_postings.blog_post_id`.

### **Controller: ScraperExecutionPipeline (run\_scraper & CLI Entry point)**

Execution orchestration managing the workflow loop.

#### **Functions & Logic**

* **run\_scraper(query="surfboard")**: Loads known Craigslist IDs, avoids detail-page requests for those listings, and saves new structured rows with linked blog posts.  
* **run\_pet\_scraper()**: Uses the East Texas community/pets URL (`cat=pet`), imports all new unique listings returned within the scraper's 24-hour freshness window, and is scheduled daily at 06:00 local time by `scheduler.py`.  
* **if \_\_name\_\_ \== "\_\_main\_\_":**: Command-line entry point reading positional CLI arguments (sys.argv\[1\]) with fallback to "surfboard".