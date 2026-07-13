"""
Canonical Role Definitions for the AI Talent Scout Platform.
"""
from __future__ import annotations

JOB_ROLES: dict[str, dict] = {
    "ML Engineer": {"skills": ["machine learning", "tensorflow", "pytorch", "scikit-learn", "python", "nlp", "computer vision"], "exp": 3, "color": "#10b981"},
    "Data Scientist": {"skills": ["machine learning", "statistics", "python", "deep learning", "sql", "feature engineering"], "exp": 4, "color": "#f59e0b"},
    "AI Research Scientist": {"skills": ["deep learning", "transformers", "research", "publications", "llm", "reinforcement learning"], "exp": 5, "color": "#ec4899"},
    "MLOps Engineer": {"skills": ["mlflow", "kubeflow", "sagemaker", "docker", "kubernetes", "model deployment"], "exp": 3, "color": "#8b5cf6"},
    "Computer Vision Engineer": {"skills": ["opencv", "yolo", "tensorrt", "image processing", "object detection"], "exp": 3, "color": "#ef4444"},
    "NLP Engineer": {"skills": ["bert", "transformers", "spacy", "llm", "sentiment analysis", "ner"], "exp": 3, "color": "#3b82f6"},
    "Data Analyst": {"skills": ["sql", "python", "pandas", "machine learning", "power bi", "tableau"], "exp": 2, "color": "#06b6d4"},
    "Data Engineer": {"skills": ["spark", "hadoop", "airflow", "kafka", "feature store", "ml pipelines"], "exp": 4, "color": "#f59e0b"},
    "Full Stack Developer": {"skills": ["react", "nodejs", "python", "django", "mongodb", "docker"], "exp": 3, "color": "#ef4444"},
    "DevOps Engineer": {"skills": ["kubernetes", "docker", "jenkins", "terraform", "aws", "mlops"], "exp": 4, "color": "#8b5cf6"},
    "Frontend Developer": {"skills": ["react", "javascript", "html", "css", "vue", "angular"], "exp": 2, "color": "#06b6d4"},
    "Backend Developer": {"skills": ["python", "django", "flask", "nodejs", "sql", "api"], "exp": 3, "color": "#ec4899"},
    "Python Developer": {"skills": ["python", "django", "flask", "pandas", "fastapi", "sqlalchemy"], "exp": 2, "color": "#f97316"},
    "Java Developer": {"skills": ["java", "spring", "hibernate", "maven", "microservices"], "exp": 3, "color": "#14b8a6"},
    "Software Engineer": {"skills": ["java", "python", "c++", "algorithms", "data structures"], "exp": 3, "color": "#6366f1"},
    "Business Analyst": {"skills": ["sql", "excel", "requirements", "jira", "agile", "stakeholder"], "exp": 3, "color": "#84cc16"},
    "Product Manager": {"skills": ["agile", "jira", "product roadmap", "stakeholder", "user stories"], "exp": 4, "color": "#f43f5e"},
    "Project Manager": {"skills": ["pmp", "agile", "scrum", "jira", "risk management"], "exp": 5, "color": "#a855f7"},
    "QA Engineer": {"skills": ["selenium", "pytest", "jira", "test cases", "automation"], "exp": 2, "color": "#eab308"},
    "Cybersecurity Analyst": {"skills": ["firewall", "siem", "penetration testing", "vulnerability"], "exp": 3, "color": "#dc2626"},
    "Cloud Engineer": {"skills": ["aws", "azure", "gcp", "terraform", "docker"], "exp": 3, "color": "#06b6d4"},
    "Blockchain Developer": {"skills": ["solidity", "ethereum", "smart contracts", "web3"], "exp": 2, "color": "#8b5cf6"},
    "Mobile Developer": {"skills": ["flutter", "react native", "swift", "kotlin"], "exp": 2, "color": "#3b82f6"},
    "iOS Developer": {"skills": ["swift", "swiftui", "xcode", "core data"], "exp": 2, "color": "#ef4444"},
    "Android Developer": {"skills": ["kotlin", "java", "android studio", "jetpack"], "exp": 2, "color": "#14b8a6"},
}
