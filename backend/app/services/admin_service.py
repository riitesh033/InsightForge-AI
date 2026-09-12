import os
from sqlalchemy.orm import Session
from sqlalchemy import func
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
        total_reports = db.query(Analysis).filter(Analysis.report_path != None).count()
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
            db.execute("SELECT 1")
        except Exception:
            db_ok = False

        # Storage Calculation
        upload_dir = settings.UPLOAD_FOLDER if hasattr(settings, 'UPLOAD_FOLDER') else "app/uploads"
        total_size = 0
        if os.path.exists(upload_dir):
            for dirpath, _, filenames in os.walk(upload_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

        return {
            "backend_status": "Operational",
            "database_status": "Healthy" if db_ok else "Degraded",
            "ai_service_status": "Connected (" + getattr(settings, 'AI_PROVIDER', 'Ollama') + ")",
            "storage_usage_mb": round(total_size / (1024 * 1024), 2)
        }