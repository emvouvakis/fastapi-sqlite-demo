## Item Management System with FastAPI and JavaScript

This project is a simple item management system built with FastAPI for the backend and plain HTML, CSS, and JavaScript for the front end. The system allows you to create, update, view, and delete items, with a Change Data Capture (CDC) feature implemented in the backend to track changes to items.

Backend (FastAPI)
- CRUD Operations: Create, Read, Update, and Delete items.
- SQLite Database: Uses SQLite for data storage.
- Change Data Capture (CDC): Tracks changes (inserts, updates, deletions) in the items table and logs them in a cdc_items table.

Frontend
- Item Form: Users can submit a form to create a new item or update an existing one.
- Items Table: Displays a list of items with their details (ID, Name, Description, Price, and Tax).
- Delete Selected Items: Allows users to select multiple items and delete them.

Getting Started

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/item-management-system.git
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the FastAPI Server**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Start Live Server and visit http://localhost:5500/ . 

**Endpoints**

- **GET /items/** : Fetch all items.
- **POST /items/** : Create a new item.
- **PUT /items/{item_id}** : Update an existing item by ID.
- **DELETE /items/{item_id}** : Delete an item by ID.
