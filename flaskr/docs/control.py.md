Here is an itemized, object-oriented structural breakdown of flaskr/control.py.

### **Object: ControlBlueprint**

A Flask Blueprint instance (bp \= Blueprint('control', \_\_name\_\_)) encapsulating views and backend dispatch services for control panel administrative features, scraper task execution, and post dataset filtering.

#### **External Dependencies**

* **clscraper**: Alias for flaskr.scrapers.craigslist.run\_scraper, the external execution engine for fetching and parsing Craigslist data.  
* **get\_db**: Database utility for retrieving current thread connection.  
* **login\_required**: Authentication decorator enforcing protected access.

### **Service: ControlPanelController**

Controller endpoint managing administrative operations via single-route branching (/control-panel).

#### **Route: control\_panel() (GET, POST /control-panel)**

* **Guard**: @login\_required (Restricts access to authenticated users).

#### **1\. Sub-Task: ScraperJobDispatcher (POST Request Branch)**

* **Conditions**: Evaluates request.method \== 'POST' and verifies presence of 'craigslist\_query' in form payload.  
* **Input Extraction**:  
  * query: Form field craigslist\_query (trimmed).  
  * radius: Form field radius (defaults to 100).  
* **Database Action**:  
  * Inserts search record into search\_query table (term, radius, status="completed", created=datetime("now")).  
  * Commits transaction to database.  
* **Execution Action**:  
  * Triggers blocking scraper task clscraper(query=query).  
* **User Feedback & Flow**:  
  * Sets success flash notification (flash(..., 'success')).  
  * Redirects to url\_for('control.control\_panel') (PRG Pattern).

#### **2\. Service: PostQueryEngine (GET Request Branch)**

* **Parameter Extraction**:  
  * status\_filter: GET query param status (defaults to 'all').  
  * search\_keyword: GET query param q (trimmed).  
  * age\_filter: GET query param age (defaults to 'all').  
* **Dynamic Query Builder**:  
  * **Base Statement**: SELECT p.id, title, body, status, created, author\_id, username FROM post p JOIN user u ON p.author\_id \= u.id WHERE 1=1  
  * **Status Clause**: Appends AND status \= ? if status\_filter \!= 'all'.  
  * **Keyword Clause**: Appends AND (title LIKE ? OR body LIKE ?) with wildcard parameters (%\<keyword\>%) if search\_keyword is non-empty.  
  * **Age Clause**:  
    * If age\_filter \== '1day': Appends AND datetime(created) \>= datetime('now', '-1 day').  
    * If age\_filter \== '7days': Appends AND datetime(created) \>= datetime('now', '-7 days').  
  * **Sorting**: Appends ORDER BY created DESC.  
* **Execution**: Executes parameterized query against SQLite database and calls .fetchall().

#### **3\. Render Response: ControlPanelViewBuilder**

* **View Render**: blog/control\_panel.html  
* **Context Payload**:  
  * posts: Array of filtered post records (filtered\_posts).  
  * status\_filter: Retained status filter string.  
  * search\_keyword: Retained search keyword string.  
  * age\_filter: Retained age filter string.