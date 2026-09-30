Here is an itemized, object-oriented structural breakdown of flaskr/control.py.

### **Object: ControlBlueprint**

A Flask Blueprint instance (bp \= Blueprint('control', \_\_name\_\_)) encapsulating views and backend dispatch services for control panel administrative features, scraper task execution, and post dataset filtering.

#### **External Dependencies**

* **run\_due\_craigslist\_jobs**: Scheduler helper that executes enabled jobs when their configured daily run times are due.  
* **get\_db**: Database utility for retrieving current thread connection.  
* **login\_required**: Authentication decorator enforcing protected access.

### **Service: ControlPanelController**

Controller endpoint managing administrative operations via single-route branching (/control-panel).

#### **Route: control\_panel() (GET, POST /control-panel)**

* **Guard**: @login\_required (Restricts access to authenticated users).

#### **CraigslistJobManager (GET, POST /control-panel/cl-jobs)**

* **Guard**: `@login_required`.
* **GET**: Lists seeded and user-configured jobs with category, term, radius, city/region, Craigslist URL, default-location status, enabled state, daily run times, and last-run timestamp. New jobs are prefilled from the default location.
* **POST add/update**: Validates the job name, search term, any current East Texas Craigslist category or subcategory code, Craigslist HTTPS location URL, radius (5–500 miles), and one or more local `HH:MM` run times. Selecting “Make default location” changes the single default while each job retains its own location.
* **Persistence**: Adds or updates rows in `craigslist_jobs`. Defaults are East Texas pets at 06:00 and surfboards/free stuff at 08:00 and 20:00. User-defined Craigslist regions can have separate search jobs.
* **Scheduler**: Checks enabled jobs each minute, runs due jobs, and records outcomes in `search_query`.

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

### **Route: system\_logs() (GET /control-panel/system-logs)**

* **Guard**: `@login_required`.
* Reads the newest 250 matching entries from the `system_logs` table.
* Supports the `level` query parameter: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`; omitting it shows all levels.
* Renders `blog/system_logs.html` with the timestamp, severity, logger name, message, source file and line, and optional exception details.