import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.user import User
from app.models.dataset import Dataset
from app.models.analysis import Analysis
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.core.config import settings

class AdminService:
    @staticmethod
    def get_dashboard_stats(db: Session):
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        total_datasets = db.query(Dataset).count()
        total_analyses = db.query(Analysis).count()
        # Reports are generated from analyses on demand and are not stored as
        # separate records, so each analysis is one report available to export.
        total_reports = total_analyses
        total_chat_messages = db.query(ChatMessage).count()
        
        avg_score = db.query(func.avg(Analysis.quality_score)).scalar() or 0.0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_datasets": total_datasets,
            "total_analyses": total_analyses,
            "total_reports": total_reports,
            "total_chat_messages": total_chat_messages,
            "avg_quality_score": round(float(avg_score), 2)
        }

    @staticmethod
    def get_system_health(db: Session):
        # DB Health
        db_ok = True
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            logging.getLogger(__name__).exception(
                "Admin database health check failed"
            )
            db_ok = False

        # Storage is measured from stored dataset records. Cloud-backed
        # datasets live in Supabase Storage and leave no local file, so
        # walking the staging directory understates usage to zero on
        # production hosts. The staging directory may also contain stray
        # leftover files that are not backed by any Dataset record; those
        # must never inflate (or override) the recorded usage.
        total_size = int(
            db.query(func.coalesce(func.sum(Dataset.file_size), 0)).scalar()
            or 0
        )

        return {
            "backend_status": "Operational",
            "database_status": "Healthy" if db_ok else "Degraded",
            "ai_service_status": "Connected (" + getattr(settings, 'AI_PROVIDER', 'Ollama') + ")",
            "storage_usage_mb": round(total_size / (1024 * 1024), 2)
        }