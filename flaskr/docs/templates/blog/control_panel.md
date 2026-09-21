Here is an itemized, object-oriented structural breakdown of flaskr/templates/blog/control\_panel.html.

### **Object: ControlPanelView**

A derived template view inheriting from BaseLayout ({% extends 'base.html' %}) that provides an administrative dashboard for dispatching web scraping jobs and filtering/managing stored posts.

#### **Properties & State Injection**

* **posts**: Collection of post objects matching active filter criteria.  
* **search\_keyword**: Active text string filter parameter (q).  
* **status\_filter**: Active status filter parameter (status).  
* **age\_filter**: Active time range filter parameter (age).

#### **Parent View Injections**

* **HeaderBlock**: Overrides {% block header %}.  
* **ContentBlock**: Overrides {% block content %}.

### **Object: HeaderBlock**

The header component injected into the base layout's header zone.

#### **Components**

* **TitleHeader**: \<h1\> containing nested Jinja2 {% block title %} displaying "Control Panel". Sets the page heading and browser tab title context.

### **Object: ContentBlock**

The primary layout viewport hosting custom component styling, a multi-column layout grid, job dispatch sidebar, and a filtered content manager.

#### **1\. Viewport Styles (ControlPanelCSS)**

* **Class Selectors:** .cp-grid, .card, .card-title, .form-group, .form-control, .btn, .filter-bar, .post-card, .badge-\*.  
* **Layout Mechanics:**  
  * Responsive 2-column CSS Grid (grid-template-columns: 1fr 2fr).  
  * Media Query breakpoint (max-width: 768px) collapsing layout to a single column on mobile viewports.

#### **2\. Layout Container: DashboardGrid (.cp-grid)**

The master CSS Grid container splitting the layout into functional regions.

### **Component: ScraperTaskSidebar (aside.sidebar)**

Left column (1fr) hosting the web scraper job dispatch form.

#### **Child Container: ScraperTaskCard (.card)**

* **CardTitle**: \<h2\> with title "New Craigslist Search".  
* **Form Object: CraigslistSearchForm**:  
  * **Attributes:** action="url\_for('control.control\_panel')", method="POST".  
  * **Controls:**  
    * **QueryInput**: \<input type="text" name="craigslist\_query" id="craigslist\_query"\> (Required text input for search keywords).  
    * **RadiusInput**: \<input type="number" name="radius" id="radius"\> (Numeric distance control: default 100, min 5, max 500).  
    * **SubmitButton**: \<button type="submit"\>Queue Search Job\</button\> (Triggers backend scraper task dispatch).

### **Component: PostManagementPanel (main.main-content)**

Right column (2fr) hosting filter parameters and rendering filtered post entries.

#### **Child Container: ManagementCard (.card)**

* **CardTitle**: \<h2\> with title "Manage & Filter Posts".

#### **1\. Form Object: FilterBarForm (.filter-bar)**

A GET request form providing parameter inputs for querying stored records.

* **Attributes:** action="url\_for('control.control\_panel')", method="GET".  
* **Controls:**  
  * **KeywordSearchInput**: Text control binding search\_keyword to query param q.  
  * **StatusFilterSelect**: Dropdown binding status\_filter to query param status ('all', 'new', 'pending', 'archived').  
  * **AgeFilterSelect**: Dropdown binding age\_filter to query param age ('all', '1day', '7days').  
  * **FilterSubmitButton**: Triggers filtered GET request.  
  * **ResetLink**: Clears query parameters by directing back to raw url\_for('control.control\_panel').

#### **2\. Container Object: PostsList (.posts-list)**

Iterative render target for dataset output.

* **Conditional Logic:**  
  * **If posts exist:** Iterates over collection to instantiate PostCard components.  
  * **Else:** Renders EmptyStateMessage (\<p\>No posts matching the selected filters were found.\</p\>).

### **Object: PostCard (article.post-card)**

A component representing an individual post item within the filtered list.

#### **Properties**

* **title**: Post record title.  
* **status**: String status identifier (new, pending, archived).  
* **username**: Author/source username string.  
* **created**: Datetime object or formatted string representing creation time.  
* **body**: HTML/text body string.

#### **Child Components**

* **PostCardHeader**: Contains title (\<h3\>) and a dynamic status badge (\<span class="badge badge-\<status\>"\>).  
* **PostCardMeta**: Displays author attribution and formatted creation timestamp (created.strftime('%Y-%m-%d %H:%M')).  
* **PostCardBody**: Renders post content using Jinja's |safe filter to support rich HTML output from scraped sources (such as external links or inline images).