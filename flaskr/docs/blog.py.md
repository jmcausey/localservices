Here is an itemized, object-oriented structural breakdown of flaskr/blog.py.

### **Object: BlogBlueprint**

A Flask Blueprint instance (bp \= Blueprint('blog', \_\_name\_\_)) encapsulating views, database operations, media processing, and API routes for blog management.

#### **Properties & Constants**

* **ALLOWED\_EXTENSIONS**: Set of valid image file extensions ({'png', 'jpg', 'jpeg', 'gif', 'webp'}).  
* **VALID\_STATUSES**: Set of acceptable workflow status strings ({'new', 'pending', 'complete'}).

### **Service: BlogHelperService**

A collection of internal utility functions handling validation, filesystem storage, row serialization, and post authorization.

#### **Methods**

* **allowed\_file(filename)**: Checks extension validity against ALLOWED\_EXTENSIONS.  
* **save\_uploaded\_image(file)**:  
  * Sanitizes filenames using secure\_filename.  
  * Ensures static target directory exists (static/media).  
  * Saves image binary and returns public relative URL string (/static/media/\<filename\>).  
* **decode\_post\_bytes(post)**: Converts sqlite3.Row to a dictionary and decodes BLOB/byte-encoded body content to UTF-8.  
* **get\_post(id, check\_author=True)**:  
  * Queries database for a post joining user author metadata.  
  * Raises 404 Not Found if record is absent.  
  * Enforces authorization check (post\['author\_id'\] \== g.user\['id'\]), raising 403 Forbidden if unauthorized.  
* **create\_post(title, body, author\_id, status='new', image\_file=None)**:  
  * Prepends HTML \<img\> tag to body content if an image file is provided.  
  * Executes SQL INSERT into the post table and commits changes.

### **Object: BlogViewRoutes**

Controller methods mapped to HTTP endpoints for rendering UI templates and handling mutations.

#### **1\. Route: index() (GET /)**

* **Query Logic**: Fetches posts created within the last 24 hours (datetime('now', '-1 day')) or posts with status 'pending', sorted newest first.  
* **View Render**: blog/index.html passing decoded posts array.

#### **2\. Route: scrolling\_view() (GET /scrolling)**

* **Query Logic**: Unfiltered fetch of all posts ordered by creation date descending.  
* **View Render**: blog/index-scrolling.html.

#### **3\. Route: kiosk\_view() (GET /kiosk)**

* **Query Logic**: Fetches raw post dictionary entries for specialized display feeds.  
* **View Render**: blog/index\_speak\_scroll.html.

#### **4\. Route: create() (GET, POST /create)**

* **Guard**: @login\_required  
* **GET Action**: Renders post composition view blog/create.html.  
* **POST Action**: Validates title presence, executes create\_post() helper, and redirects to blog.index.

#### **5\. Route: update(id) (GET, POST /\<id\>/update)**

* **Guard**: @login\_required  
* **GET Action**: Fetches authorized post via get\_post(id) and renders blog/update.html.  
* **POST Action**: Handles post field updates, image replacement prepending, executes database UPDATE, and redirects to blog.index.

#### **6\. Route: delete(id) (POST /\<id\>/delete)**

* **Guard**: @login\_required  
* **Action**: Verifies ownership via get\_post(id), executes database DELETE, and redirects to blog.index.

#### **7\. Route: change\_status(id, new\_status) (GET, POST /\<id\>/status/\<new\_status\>)**

* **Guard**: @login\_required  
* **Action**: Sanitizes status string (e.g., mapping 'completed' $\\rightarrow$ 'complete'), validates against VALID\_STATUSES, checks ownership, executes status SQL UPDATE, and redirects to blog.index.

### **Service: AudioAndAPIService**

API and streaming media services exposing endpoints for async clients and Text-to-Speech (TTS) generation.

#### **Methods & Endpoints**

* **latest\_post\_id() (GET /api/latest-post-id)**:  
  * Queries MAX(id) from post table.  
  * **Response**: JSON payload {"latest\_id": \<int\>} used by client polling scripts.  
* **get\_post\_audio(id) (GET /audio/\<id\>)**:  
  * Queries title and body for post id.  
  * Strips HTML formatting tags using BeautifulSoup (BeautifulSoup.get\_text()).  
  * Converts clean text to spoken audio stream via gTTS (gTTS(text, lang='en')).  
  * **Response**: Audio stream payload (send\_file) served with MIME type audio/mpeg.