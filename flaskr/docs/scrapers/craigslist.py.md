Here is an itemized, object-oriented structural breakdown of flaskr/scrapers/craigslist.py.

### **Module: CraigslistScraperModule**

A specialized web scraping script that extracts item listings from Craigslist near Athens, TX (zip code 75751), processes media and pricing metadata, performs batch and database deduplication, and persists formatted records into the application's blog post store.

#### **Constants & Environment Setup**

* **root\_dir**: System path resolution dynamically locating and prepending the application root directory to sys.path.  
* **BASE\_URL**: Target Craigslist endpoint (\[https://easttexas.craigslist.org/search/sss\](https://easttexas.craigslist.org/search/sss)).

### **Service: CraigslistScraperEngine (get\_craigslist\_listings)**

Scrapes, parses, and converts search listings into HTML blog post payloads.

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
> 5. **URL Formatting**: Converts relative URL paths into absolute links (\[https://dallas.craigslist.org/\](https://dallas.craigslist.org/)...).  
> 6. **In-Memory Batch Deduplication**: Maintains a seen\_titles set to skip duplicate titles parsed from the current page payload.  
> 7. **Detail Page Metadata Extraction**: Dispatches secondary HTTP requests to listing detail pages to extract OpenGraph preview images (meta\[property="og:image"\]).  
> 8. **HTML Payload Generation**: Formats the title (\<CapitalizedQuery\>: \<Title\> (\<Price\>)) and body containing formatted HTML markup, pricing information, dynamic image tags, and original post links.

### **Service: ScrapedDataPersistenceService (insert\_scraped\_post)**

Database interface layer handling persistence of scraped items.

#### **Execution Flow & Database Constraints**

* **Context Creation**: Spawns temporary application contexts using create\_app().  
* **Database Deduplication**: Checks post table for existing matching title records prior to insertion.  
* **Insertion Payload**: Binds parameters and inserts new records (author\_id, title, body, status) into the post database table with default status 'new'.

### **Controller: ScraperExecutionPipeline (run\_scraper & CLI Entry point)**

Execution orchestration managing the workflow loop.

#### **Functions & Logic**

* **run\_scraper(query="surfboard")**: Orchestrates sequential processing by passing results from get\_craigslist\_listings directly into insert\_scraped\_post.  
* **if \_\_name\_\_ \== "\_\_main\_\_":**: Command-line entry point reading positional CLI arguments (sys.argv\[1\]) with fallback to "surfboard".