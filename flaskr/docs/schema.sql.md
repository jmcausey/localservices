Here is an itemized, object-oriented structural breakdown of flaskr/schema.sql.

### **Object: DatabaseSchema**

The core SQL initialization script defining table structures, field types, constraints, default values, generated columns, and index optimizations for the application.

#### **Tear-Down Statements**

* **Drops existing tables** sequentially to ensure clean recreation: user, post, chart, gallary (typo variant drop), network\_logs, and astronomy.

### **Entities & Data Models**

#### **1\. Entity: user**

Stores authentication profiles for application users.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **username**: TEXT (Unique, Not Null)  
* **password**: TEXT (Hashed password payload, Not Null)

#### **2\. Entity: post**

Stores blog entries and publishing workflow state.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **author\_id**: INTEGER (Foreign Key referencing user(id), Not Null)  
* **created**: TIMESTAMP (Not Null, Defaults to CURRENT\_TIMESTAMP)  
* **title**: TEXT (Not Null)  
* **body**: BLOB (Binary post content, Not Null)  
* **image**: TEXT (Relative static path to media file)  
* **status**: TEXT (Workflow state, Defaults to 'new')

#### **3\. Entity: chart**

Stores meteorological readings and calculates derived atmospheric metrics.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **created\_at**: DATETIME (Defaults to local timestamp via datetime('now', 'localtime'))  
* **location**: TEXT (Not Null)  
* **geolocation**, **description**: TEXT  
* **temperature**, **feelslike**, **windspeed**: REAL  
* **pressure**, **humidity**, **visibility**, **winddirection**, **clouds**: INTEGER  
* **sunrise**, **sunset**: DATETIME  
* **dew\_point**: REAL (**Generated Stored Column**)  
  * Uses Magnus formula approximation:  
    $$\\text{dew\\\_point} \= \\text{CAST}\\left(\\text{ROUND}\\left(\\frac{237.3 \\cdot \\gamma}{17.27 \- \\gamma}\\right) \\text{ AS INTEGER}\\right)$$  
    where $\\gamma \= \\ln\\left(\\frac{\\text{humidity}}{100.0}\\right) \+ \\frac{17.27 \\cdot \\text{temperature}}{\\text{temperature} \+ 237.3}$

#### **4\. Entity: gallery**

Stores raw image binary files directly inside SQLite.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **filename**: TEXT (Not Null)  
* **image\_data**: BLOB (Raw image binary, Not Null)

#### **5\. Entity: network\_logs**

Logs network packet events and host discovery results.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **timestamp**: TEXT (Defaults to UTC ISO string DATETIME('now'), Not Null)  
* **source\_ip**, **dest\_ip**: TEXT (Not Null)  
* **source\_port**, **dest\_port**: INTEGER  
* **protocol**: TEXT (Not Null, e.g., 'ARP', 'TCP')  
* **bytes\_sent**, **bytes\_received**: INTEGER (Defaults to 0\)  
* **status**, **message**: TEXT

#### **6\. Entity: astronomy**

Stores comprehensive solar, lunar, and twilight telemetry queried from external APIs.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **timestamp**: TEXT (Not Null, Defaults to DATETIME('now'))  
* **Location Metrics**: location, country\_name, state\_prov, city, locality (TEXT); latitude, longitude, elevation (REAL).  
* **Sun & Solar Metrics**: sunrise, sunset, solar\_noon, day\_length, sun\_status (TEXT); sun\_altitude, sun\_distance, sun\_azimuth (REAL).  
* **Twilight & Hour Timings**: mid\_night, night\_end, night\_begin, morn\_\*\_twilight\_\*, eve\_\*\_twilight\_\*, morn\_blue\_hour\_\*, morn\_golden\_hour\_\*, eve\_blue\_hour\_\*, eve\_golden\_hour\_\* (TEXT).  
* **Moon & Lunar Metrics**: moon\_phase, moonrise, moonset, moon\_status (TEXT); moon\_altitude, moon\_distance, moon\_azimuth, moon\_parallactic\_angle, moon\_illumination\_percentage, moon\_angle (REAL).

#### **7\. Entity: search\_query**

Tracks automated scraping requests dispatched via control panel routines.

* **id**: INTEGER (Primary Key, Autoincrement)  
* **term**: TEXT (Search keyword, Not Null)  
* **radius**: INTEGER (Geographic query radius, Not Null)  
* **status**: TEXT (Execution state, Not Null)  
* **created**: TIMESTAMP (Defaults to CURRENT\_TIMESTAMP, Not Null)

### **Performance Index Optimization**

Indexes created to optimize query filtering on high-volume diagnostic tables:

* **idx\_network\_logs\_timestamp**: B-tree index on network\_logs(timestamp).  
* **idx\_network\_logs\_source\_ip**: B-tree index on network\_logs(source\_ip).