from app.repositories.base_repository import BaseRepository
from app.database.models import Resume, Analysis

class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db):
        super().__init__(Resume, db)

class AnalysisRepository(BaseRepository[Analysis]):
    def __init__(self, db):
        super().__init__(Analysis, db)
