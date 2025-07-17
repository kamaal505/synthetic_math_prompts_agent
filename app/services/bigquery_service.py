"""
BigQuery service layer to handle database operations using direct BigQuery client.
This replaces SQLAlchemy operations for better performance and compatibility.
"""

from google.cloud import bigquery
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from decimal import Decimal
from app.config import settings
import uuid

class BigQueryService:
    def __init__(self, project_id: str = None, dataset_id: str = None):
        # Use config settings if not provided
        if project_id is None:
            project_id = settings.BIGQUERY_PROJECT_ID
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET_ID
            
        self.client = bigquery.Client(project=project_id)
        self.dataset_ref = self.client.dataset(dataset_id)
        self.batches_table = f"{project_id}.{dataset_id}.batches"
        self.problems_table = f"{project_id}.{dataset_id}.problems"
    
    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string for BigQuery storage."""
        if data is None:
            return None
        if isinstance(data, dict):
            return json.dumps(data)
        return str(data)
    
    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string from BigQuery."""
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime for BigQuery timestamp."""
        if dt is None:
            return None
        return dt.isoformat()
    
    def _format_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for BigQuery."""
        if value is None:
            return None
        return float(value)

    def _generate_unique_id(self) -> int:
        """Generate a unique 64-bit integer ID."""
        return uuid.uuid4().int & ((1 << 63) - 1)

    # Batch Operations
    def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new batch record."""
        # Generate a unique ID if not provided
        if not batch_data.get("id"):
            batch_data["id"] = self._generate_unique_id()
        query = f"""
        INSERT INTO `{self.batches_table}` 
        (id, name, taxonomy_json, pipeline, num_problems, batch_cost, created_at, updated_at)
        VALUES (
            @id, @name, @taxonomy_json, @pipeline, @num_problems, @batch_cost, 
            CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id", "INT64", batch_data["id"]),
                bigquery.ScalarQueryParameter("name", "STRING", batch_data.get("name")),
                bigquery.ScalarQueryParameter("taxonomy_json", "STRING", 
                                            self._serialize_json(batch_data.get("taxonomy_json"))),
                bigquery.ScalarQueryParameter("pipeline", "STRING", 
                                            self._serialize_json(batch_data.get("pipeline"))),
                bigquery.ScalarQueryParameter("num_problems", "INT64", batch_data.get("num_problems")),
                bigquery.ScalarQueryParameter("batch_cost", "FLOAT64", 
                                            self._format_decimal(batch_data.get("batch_cost", 0.0))),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to complete
        
        # Get the created batch by id
        return self.get_batch(batch_data["id"])
    
    def get_batch(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """Get a batch by ID."""
        query = f"""
        SELECT * FROM `{self.batches_table}`
        WHERE CAST(id AS STRING) = @batch_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return {
                "id": row.id,
                "name": row.name,
                "taxonomy_json": self._deserialize_json(row.taxonomy_json),
                "pipeline": self._deserialize_json(row.pipeline),
                "num_problems": row.num_problems,
                "batch_cost": row.batch_cost,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            }
        return None
    
    def get_batch_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a batch by name."""
        query = f"""
        SELECT * FROM `{self.batches_table}`
        WHERE name = @name
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("name", "STRING", name),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return {
                "id": row.id,
                "name": row.name,
                "taxonomy_json": self._deserialize_json(row.taxonomy_json),
                "pipeline": self._deserialize_json(row.pipeline),
                "num_problems": row.num_problems,
                "batch_cost": row.batch_cost,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            }
        return None
    
    def get_batches(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all batches with pagination."""
        query = f"""
        SELECT * FROM `{self.batches_table}`
        ORDER BY created_at DESC
        LIMIT @limit OFFSET @skip
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
                bigquery.ScalarQueryParameter("skip", "INT64", skip),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        batches = []
        for row in results:
            batches.append({
                "id": row.id,
                "name": row.name,
                "taxonomy_json": self._deserialize_json(row.taxonomy_json),
                "pipeline": self._deserialize_json(row.pipeline),
                "num_problems": row.num_problems,
                "batch_cost": row.batch_cost,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return batches
    
    def update_batch_cost(self, batch_id: int, cost: float) -> bool:
        """Update batch cost."""
        query = f"""
        UPDATE `{self.batches_table}`
        SET batch_cost = @cost, updated_at = CURRENT_TIMESTAMP()
        WHERE CAST(id AS STRING) = @batch_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("cost", "FLOAT64", cost),
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()
        return True
    
    def delete_batch(self, batch_id: int) -> bool:
        """Delete a batch and its associated problems."""
        # First delete associated problems
        self.delete_problems_by_batch(batch_id)
        
        # Then delete the batch
        query = f"""
        DELETE FROM `{self.batches_table}`
        WHERE CAST(id AS STRING) = @batch_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()
        return True

    # Problem Operations
    def create_problem(self, problem_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new problem record."""
        # Generate a unique ID if not provided
        if not problem_data.get("id"):
            problem_data["id"] = self._generate_unique_id()
        query = f"""
        INSERT INTO `{self.problems_table}` 
        (id, subject, topic, question, answer, hints, rejection_reason, status, batch_id, 
         problem_embedding, similar_problems, cost, target_model_answer, hints_were_corrected, 
         reference, created_at, updated_at)
        VALUES (
            @id, @subject, @topic, @question, @answer, @hints, @rejection_reason, @status, @batch_id,
            @problem_embedding, @similar_problems, @cost, @target_model_answer, @hints_were_corrected,
            @reference, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("id", "INT64", problem_data["id"]),
                bigquery.ScalarQueryParameter("subject", "STRING", problem_data.get("subject")),
                bigquery.ScalarQueryParameter("topic", "STRING", problem_data.get("topic")),
                bigquery.ScalarQueryParameter("question", "STRING", problem_data.get("question")),
                bigquery.ScalarQueryParameter("answer", "STRING", problem_data.get("answer")),
                bigquery.ScalarQueryParameter("hints", "STRING", 
                                            self._serialize_json(problem_data.get("hints"))),
                bigquery.ScalarQueryParameter("rejection_reason", "STRING", 
                                            problem_data.get("rejection_reason")),
                bigquery.ScalarQueryParameter("status", "STRING", problem_data.get("status")),
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(problem_data.get("batch_id"))),
                bigquery.ScalarQueryParameter("problem_embedding", "STRING", 
                                            self._serialize_json(problem_data.get("problem_embedding"))),
                bigquery.ScalarQueryParameter("similar_problems", "STRING", 
                                            self._serialize_json(problem_data.get("similar_problems", {}))),
                bigquery.ScalarQueryParameter("cost", "FLOAT64", 
                                            self._format_decimal(problem_data.get("cost", 0.0))),
                bigquery.ScalarQueryParameter("target_model_answer", "STRING", 
                                            problem_data.get("target_model_answer")),
                bigquery.ScalarQueryParameter("hints_were_corrected", "INT64", 
                                            int(problem_data.get("hints_were_corrected", 0))),
                bigquery.ScalarQueryParameter("reference", "STRING", 
                                            problem_data.get("reference")),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()
        
        # Return the created problem by id
        return self.get_problem(problem_data["id"])
    
    def get_problem(self, problem_id: int) -> Optional[Dict[str, Any]]:
        """Get a problem by ID."""
        query = f"""
        SELECT * FROM `{self.problems_table}`
        WHERE CAST(id AS STRING) = @problem_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("problem_id", "STRING", str(problem_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return self._row_to_problem_dict(row)
        return None
    
    def get_problem_by_batch_and_subject(self, batch_id: int, subject: str, question: str) -> Optional[Dict[str, Any]]:
        """Get a problem by batch_id, subject, and question."""
        query = f"""
        SELECT * FROM `{self.problems_table}`
        WHERE CAST(batch_id AS STRING) = @batch_id AND subject = @subject AND question = @question
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
                bigquery.ScalarQueryParameter("subject", "STRING", subject),
                bigquery.ScalarQueryParameter("question", "STRING", question),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            return self._row_to_problem_dict(results[0])
        return None
    
    def get_problems(self, skip: int = 0, limit: int = 1000, 
                    batch_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get problems with filtering and pagination."""
        where_conditions = []
        parameters = []
        
        if batch_id:
            where_conditions.append("CAST(batch_id AS STRING) = @batch_id")
            parameters.append(bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)))
        
        if status:
            where_conditions.append("status = @status")
            parameters.append(bigquery.ScalarQueryParameter("status", "STRING", status))
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT * FROM `{self.problems_table}`
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT @limit OFFSET @skip
        """
        
        parameters.extend([
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("skip", "INT64", skip),
        ])
        
        job_config = bigquery.QueryJobConfig(query_parameters=parameters)
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        problems = []
        for row in results:
            problems.append(self._row_to_problem_dict(row))
        
        return problems
    
    def get_problems_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """Get all problems for a specific batch."""
        return self.get_problems(batch_id=batch_id, limit=10000)
    
    def delete_problems_by_batch(self, batch_id: int) -> bool:
        """Delete all problems for a specific batch."""
        query = f"""
        DELETE FROM `{self.problems_table}`
        WHERE CAST(batch_id AS STRING) = @batch_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        query_job.result()
        return True
    
    def get_problem_stats(self, batch_id: int) -> Dict[str, int]:
        """Get problem statistics for a batch."""
        query = f"""
        SELECT 
            status,
            COUNT(*) as count
        FROM `{self.problems_table}`
        WHERE CAST(batch_id AS STRING) = @batch_id
        GROUP BY status
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id)),
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        stats = {"discarded": 0, "valid": 0, "solved": 0}
        for row in results:
            stats[row.status] = row.count
        
        return stats
    
    def get_problems_count(self, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """Get the number of problems."""
        if batch_id:
            query = f"""
            SELECT COUNT(*) as count
            FROM `{self.problems_table}`
            WHERE CAST(batch_id AS STRING) = @batch_id
            """
            parameters = [bigquery.ScalarQueryParameter("batch_id", "STRING", str(batch_id))]
        else:
            query = f"""
            SELECT COUNT(*) as count
            FROM `{self.problems_table}`
            """
            parameters = []
        
        job_config = bigquery.QueryJobConfig(query_parameters=parameters)
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        count = results[0].count if results else 0
        
        if batch_id:
            return {"batch_id": batch_id, "problems_count": count}
        else:
            return {"total_problems_count": count}
    
    def _row_to_problem_dict(self, row) -> Dict[str, Any]:
        """Convert a BigQuery row to a problem dictionary."""
        return {
            "id": row.id,
            "subject": row.subject,
            "topic": row.topic,
            "question": row.question,
            "answer": row.answer,
            "hints": self._deserialize_json(row.hints),
            "rejection_reason": row.rejection_reason,
            "status": row.status,
            "batch_id": row.batch_id,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "problem_embedding": self._deserialize_json(row.problem_embedding),
            "similar_problems": self._deserialize_json(row.similar_problems),
            "cost": row.cost,
            "target_model_answer": row.target_model_answer,
            "hints_were_corrected": row.hints_were_corrected,
            "reference": row.reference
        }

# Global instance
bigquery_service = BigQueryService() 