from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Dict, Any, List
import json
from config import DATABASE_URL

Base = declarative_base()

class Dataset(Base):
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=False)
    row_count = Column(Integer)
    column_count = Column(Integer)
    data_quality = Column(JSON)
    column_info = Column(JSON)
    
    queries = relationship("Query", back_populates="dataset")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_time': self.upload_time.isoformat(),
            'file_path': self.file_path,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'data_quality': self.data_quality,
            'column_info': self.column_info
        }

class Query(Base):
    __tablename__ = 'queries'
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    query_text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Float)  # in seconds
    success = Column(String, nullable=False)  # 'success' or 'error'
    error_message = Column(String)
    result = Column(JSON)
    
    dataset = relationship("Dataset", back_populates="queries")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'query_text': self.query_text,
            'timestamp': self.timestamp.isoformat(),
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message,
            'result': self.result
        }

# Create database engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DatabaseManager:
    def __init__(self):
        self.SessionLocal = SessionLocal
    
    def create_dataset(self, dataset_info: Dict[str, Any]) -> Dataset:
        """Create a new dataset record."""
        with self.SessionLocal() as session:
            dataset = Dataset(
                filename=dataset_info['filename'],
                file_path=dataset_info['file_path'],
                row_count=dataset_info.get('row_count'),
                column_count=dataset_info.get('column_count'),
                data_quality=dataset_info.get('data_quality'),
                column_info=dataset_info.get('column_info')
            )
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset
    
    def log_query(
        self,
        dataset_id: int,
        query_text: str,
        execution_time: float,
        success: bool,
        result: Dict[str, Any] = None,
        error_message: str = None
    ) -> Query:
        """Log a query execution."""
        with self.SessionLocal() as session:
            query = Query(
                dataset_id=dataset_id,
                query_text=query_text,
                execution_time=execution_time,
                success='success' if success else 'error',
                result=result,
                error_message=error_message
            )
            session.add(query)
            session.commit()
            session.refresh(query)
            return query
    
    def get_dataset_history(self, dataset_id: int) -> List[Dict[str, Any]]:
        """Get query history for a dataset."""
        with self.SessionLocal() as session:
            queries = session.query(Query).filter(
                Query.dataset_id == dataset_id
            ).order_by(Query.timestamp.desc()).all()
            return [query.to_dict() for query in queries]
    
    def get_similar_queries(
        self,
        query_text: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get similar queries that were executed before."""
        with self.SessionLocal() as session:
            # Simple similarity based on common words
            query_words = set(query_text.lower().split())
            all_queries = session.query(Query).filter(
                Query.success == 'success'
            ).order_by(Query.timestamp.desc()).limit(100).all()
            
            similar_queries = []
            for query in all_queries:
                stored_words = set(query.query_text.lower().split())
                similarity = len(query_words & stored_words) / len(query_words | stored_words)
                if similarity > 0.3:  # Arbitrary threshold
                    similar_queries.append((similarity, query))
            
            similar_queries.sort(reverse=True)
            return [query.to_dict() for _, query in similar_queries[:limit]]
    
    def get_dataset_insights(self, dataset_id: int) -> Dict[str, Any]:
        """Get insights about the dataset's usage."""
        with self.SessionLocal() as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return None
            
            queries = session.query(Query).filter(
                Query.dataset_id == dataset_id
            ).all()
            
            successful_queries = [q for q in queries if q.success == 'success']
            error_queries = [q for q in queries if q.success == 'error']
            
            return {
                'dataset_info': dataset.to_dict(),
                'query_stats': {
                    'total_queries': len(queries),
                    'successful_queries': len(successful_queries),
                    'error_queries': len(error_queries),
                    'avg_execution_time': sum(q.execution_time for q in queries) / len(queries) if queries else 0
                },
                'recent_queries': [q.to_dict() for q in queries[-5:]],
                'common_errors': self._analyze_errors(error_queries)
            }
    
    def _analyze_errors(self, error_queries: List[Query]) -> List[Dict[str, Any]]:
        """Analyze common error patterns in failed queries."""
        error_patterns = {}
        for query in error_queries:
            if query.error_message:
                error_type = query.error_message.split(':')[0]
                if error_type in error_patterns:
                    error_patterns[error_type]['count'] += 1
                    error_patterns[error_type]['examples'].append(query.query_text)
                else:
                    error_patterns[error_type] = {
                        'count': 1,
                        'examples': [query.query_text]
                    }
        
        return [
            {
                'error_type': error_type,
                'count': data['count'],
                'example_queries': data['examples'][:3]
            }
            for error_type, data in sorted(
                error_patterns.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
        ]