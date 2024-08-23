import uuid
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DDL, event, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to capture detailed logs
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"], # URL OF FRONTEND
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = "sqlite:///./sqlite.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Item model
class ItemInDB(Base):
    __tablename__ = "items"
    id = Column(String(36), primary_key=True, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, index=True)
    description = Column(String(300), nullable=True)
    price = Column(Float, nullable=False)
    tax = Column(Float, default=0)

# Create the cdc_items table with a foreign key to the items table
class CDCItem(Base):
    __tablename__ = "cdc_items"
    cdc_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(36),  index=True)
    name = Column(String(50), index=True)
    description = Column(String(300), nullable=True)
    price = Column(Float, nullable=False)
    tax = Column(Float, default=0)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    action = Column(String(10), nullable=False)  # 'insert', 'update', 'delete'

# Create the database tables
Base.metadata.create_all(bind=engine)

# Define the Pydantic Item model for validation
class Item(BaseModel):
    name: str = Field(max_length=50, description="The name of the item")
    description: Optional[str] = Field(None, max_length=300, description="A brief description of the item")
    price: float = Field(gt=0, description="The price of the item, must be greater than 0")
    tax: Optional[float] = Field(0, ge=0, description="The tax on the item, must be 0 or positive")

# Pydantic model for response validation
class ItemResponse(BaseModel):
    item_id: str
    item: Item

# Function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create triggers for CDC
trigger_insert = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_insert_cdc_items
AFTER INSERT ON items
FOR EACH ROW
BEGIN
    INSERT INTO cdc_items (id, name, description, price, tax, action)
    VALUES (NEW.id, NEW.name, NEW.description, NEW.price, NEW.tax, 'insert');
END;
""")

trigger_update = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_update_cdc_items
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    INSERT INTO cdc_items (id, name, description, price, tax, action)
    VALUES (NEW.id, NEW.name, NEW.description, NEW.price, NEW.tax, 'update');
END;
""")

trigger_delete = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_delete_cdc_items
BEFORE DELETE ON items
FOR EACH ROW
BEGIN
    INSERT INTO cdc_items (id, name, description, price, tax, action)
    VALUES (OLD.id, OLD.name, OLD.description, OLD.price, OLD.tax, 'delete');
END;
""")

# Bind the triggers to the engine
event.listen(Base.metadata, 'after_create', trigger_insert)
event.listen(Base.metadata, 'after_create', trigger_update)
event.listen(Base.metadata, 'after_create', trigger_delete)

# Recreate the database tables and triggers
Base.metadata.create_all(bind=engine)

# Get all items
@app.get("/items/", response_model=List[ItemResponse])
async def get_all_items(db: Session = Depends(get_db)):
    
    try:
        items = db.query(ItemInDB).all()
        return [{"item_id": item.id, "item": item} for item in items]

    except:
        # Log general errors
        logger.error(f"Unexpected error while getting all items: {e}")


# Insert new item
@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item, db: Session = Depends(get_db)):

    try:
        db_item = ItemInDB(**item.dict())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        # Log successful insert
        logger.info(f"Item with ID {db_item.id} inserted successfully.")

        return {"message": "Item created", "item_id": db_item.id, "item": item}

    except Exception as e:
        # Log general errors
        logger.error(f"Unexpected error while inserting item with ID {item_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Update item by ID
@app.put("/items/{item_id}", status_code=status.HTTP_200_OK)
async def update_item(item_id: str, item: Item, db: Session = Depends(get_db)):

    try:
        db_item = db.query(ItemInDB).filter(ItemInDB.id == item_id).first()
        
        for key, value in item.dict().items():
            setattr(db_item, key, value)
        
        db.commit()
        db.refresh(db_item)

        # Log successful update
        logger.info(f"Item with ID {item_id} updated successfully.")

        return {"message": "Item updated", "item": item}
        
    except Exception as e:
        # Log general errors
        logger.error(f"Unexpected error while updating item with ID {item_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str, db: Session = Depends(get_db)):
    try:
        # Fetch the item
        db_item = db.query(ItemInDB).filter(ItemInDB.id == item_id).first()
        
        if db_item:

            # Delete the item
            db.delete(db_item)
            db.commit()
            
            # Log successful deletion
            logger.info(f"Item with ID {item_id} deleted successfully.")
            return {"message": "Item deleted"}
        else:
            # Log the absence of the item
            logger.warning(f"Item with ID {item_id} not found.")
            raise HTTPException(status_code=404, detail="Item not found")
    
    except Exception as e:
        # Log general errors
        logger.error(f"Unexpected error while deleting item with ID {item_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")