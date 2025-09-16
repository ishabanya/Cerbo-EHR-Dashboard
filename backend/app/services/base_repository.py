from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc
from ..models.base import Base
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base repository class with common CRUD operations
    """
    
    def __init__(self, model: type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with ID: {db_obj.id}")
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            self.db.rollback()
            raise
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ID {id}: {e}")
            raise
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        order_by: str = None,
        order_direction: str = "asc"
    ) -> List[ModelType]:
        """Get all records with pagination and ordering"""
        try:
            query = self.db.query(self.model)
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            raise
    
    def update(self, id: int, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record by ID"""
        try:
            db_obj = self.get_by_id(id)
            if not db_obj:
                return None
            
            for field, value in obj_data.items():
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__} with ID: {id}")
            return db_obj
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__} with ID {id}: {e}")
            self.db.rollback()
            raise
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        try:
            db_obj = self.get_by_id(id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            logger.info(f"Deleted {self.model.__name__} with ID: {id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} with ID {id}: {e}")
            self.db.rollback()
            raise
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Count records with optional filters"""
        try:
            query = self.db.query(self.model)
            
            if filters:
                query = self._apply_filters(query, filters)
            
            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            raise
    
    def exists(self, id: int) -> bool:
        """Check if a record exists by ID"""
        try:
            return self.db.query(
                self.db.query(self.model).filter(self.model.id == id).exists()
            ).scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model.__name__} with ID {id}: {e}")
            raise
    
    def get_by_field(self, field_name: str, field_value: Any) -> Optional[ModelType]:
        """Get a record by a specific field"""
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"Field {field_name} does not exist on {self.model.__name__}")
            
            field = getattr(self.model, field_name)
            return self.db.query(self.model).filter(field == field_value).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by {field_name}: {e}")
            raise
    
    def get_by_fields(self, filters: Dict[str, Any]) -> List[ModelType]:
        """Get records by multiple field criteria"""
        try:
            query = self.db.query(self.model)
            query = self._apply_filters(query, filters)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by fields: {e}")
            raise
    
    def search(
        self, 
        search_fields: List[str], 
        search_term: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """Search records across multiple fields"""
        try:
            if not search_term:
                return []
            
            query = self.db.query(self.model)
            
            # Build OR conditions for each search field
            or_conditions = []
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    or_conditions.append(field.ilike(f"%{search_term}%"))
            
            if or_conditions:
                query = query.filter(or_(*or_conditions))
            
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching {self.model.__name__}: {e}")
            raise
    
    def bulk_create(self, obj_data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records in bulk"""
        try:
            db_objs = [self.model(**obj_data) for obj_data in obj_data_list]
            self.db.add_all(db_objs)
            self.db.commit()
            
            for db_obj in db_objs:
                self.db.refresh(db_obj)
            
            logger.info(f"Created {len(db_objs)} {self.model.__name__} records")
            return db_objs
        except SQLAlchemyError as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            self.db.rollback()
            raise
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> List[ModelType]:
        """Update multiple records in bulk"""
        try:
            updated_objs = []
            
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                obj_id = update_data.pop('id')
                db_obj = self.get_by_id(obj_id)
                
                if db_obj:
                    for field, value in update_data.items():
                        if hasattr(db_obj, field) and value is not None:
                            setattr(db_obj, field, value)
                    updated_objs.append(db_obj)
            
            self.db.commit()
            
            for db_obj in updated_objs:
                self.db.refresh(db_obj)
            
            logger.info(f"Updated {len(updated_objs)} {self.model.__name__} records")
            return updated_objs
        except SQLAlchemyError as e:
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            self.db.rollback()
            raise
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to a query"""
        for field_name, field_value in filters.items():
            if hasattr(self.model, field_name) and field_value is not None:
                field = getattr(self.model, field_name)
                
                # Handle different filter types
                if isinstance(field_value, dict):
                    # Support for range queries, etc.
                    if 'gte' in field_value:
                        query = query.filter(field >= field_value['gte'])
                    if 'lte' in field_value:
                        query = query.filter(field <= field_value['lte'])
                    if 'in' in field_value:
                        query = query.filter(field.in_(field_value['in']))
                    if 'like' in field_value:
                        query = query.filter(field.ilike(f"%{field_value['like']}%"))
                else:
                    # Direct equality
                    query = query.filter(field == field_value)
        
        return query