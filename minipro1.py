import streamlit as st
import re
import io
import os
import joblib
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from fpdf import FPDF
import warnings
warnings.filterwarnings('ignore')

def display_resume_review(resume_review_data):
    """Display comprehensive resume review section with enhanced dashboard label"""
    st.markdown("## 📋 **Overall Resume Review**")
    
    # Overall Score
    review_score = 0
    if resume_review_data["has_contact"]: review_score += 20
    if len(resume_review_data["sections_found"]) >= 3: review_score += 20
    if resume_review_data["action_verbs"] >= 3: review_score += 20
    if resume_review_data["has_quant"]: review_score += 15
    if 150 <= resume_review_data["word_count"] <= 400: review_score += 15
    if resume_review_data["has_github"] or resume_review_data["has_portfolio"]: review_score += 10
    
    score_class = (
        "excellent" if review_score >= 80 else
        "good" if review_score >= 60 else
        "average" if review_score >= 40 else
        "needs-work"
    )
    
    col1, col2 = st.columns([1, 3])
    
    # LEFT CARD (Score)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-title">Resume Quality</div>
            <div style="font-size: 2.5rem; font-weight: bold; color: white;">{review_score}%</div>
            <div style="font-size: 0.9rem; opacity: 0.9;">Overall Score</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # RIGHT CARD (FIXED — Now content inside box properly)
    with col2:
        
        # Generate reason text FIRST
        if review_score >= 80:
            reason_text = "✅ <b>Excellent Resume</b><br>Professional, complete, and ATS-optimized."
        elif review_score >= 60:
            reason_text = "✅ <b>Good Resume</b><br>Solid foundation with minor improvements needed."
        elif review_score >= 40:
            reason_text = "⚠️ <b>Average Resume</b><br>Missing key sections and achievements."
        else:
            reason_text = "❌ <b>Needs Work</b><br>Major gaps in structure and content."

        # SINGLE HTML BLOCK (Very Important Fix)
        st.markdown(f"""
        <div class="reason-card {score_class}">
            {reason_text}
        </div>
        """, unsafe_allow_html=True)

    # -----------------------
    # Quick Assessment
    # -----------------------
    st.markdown("### **📊 Quick Assessment**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 Sections Found", len(resume_review_data["sections_found"]))
        if resume_review_data["sections_found"]:
            st.info("• " + " • ".join(resume_review_data["sections_found"][:3]))
    
    with col2:
        st.metric("⚡ Action Verbs", resume_review_data["action_verbs"])
        st.caption("developed, designed, implemented, etc.")
    
    with col3:
        st.metric("📏 Word Count", f"{resume_review_data['word_count']:,}")
        st.caption(resume_review_data["length_status"])
    
    # -----------------------
    # Checklist
    # -----------------------
    st.markdown("### **✅ Professional Checklist**")
    
    checklist_items = [
        ("Contact Info", resume_review_data["has_contact"]),
        ("Quantifiable Results", resume_review_data["has_quant"]),
        ("GitHub/Portfolio", resume_review_data["has_github"] or resume_review_data["has_portfolio"]),
        ("ATS Keywords", resume_review_data["action_verbs"] >= 2)
    ]
    
    for item_name, is_good in checklist_items:
        status_emoji = "✅" if is_good else "❌"
        st.markdown(f"**{status_emoji} {item_name}**")


def display_skill_gap_analysis(results):
    """Display the fixed skill gap analysis section"""
    st.markdown("### **🎯 Skill Gap Analysis**")
    role_skills = results['role_data']['skills']
    full_resume_lower = results['full_resume'].lower()

    found_skills = []
    missing_skills = []

    for skill in role_skills:
        if skill.lower() in full_resume_lower:
            found_skills.append(skill)
        else:
            missing_skills.append(skill)

    col1, col2 = st.columns(2)

    with col1:
        st.success(f"✅ **Skills Found** ({len(found_skills)}/{len(role_skills)})")
        if found_skills:
            st.info("• " + " • ".join([s.title() for s in found_skills[:6]]))
        else:
            st.info("No matching skills found")

    with col2:
        if missing_skills:
            st.error(f"❌ **Skills to Learn** ({len(missing_skills)})")
            st.warning("• " + " • ".join([s.title() for s in missing_skills[:6]]))
        else:
            st.success("🎉 **All skills matched!**")

def display_skill_coverage(results):
    """Display the new skill coverage analysis for multiple mode securely"""
    st.markdown("### **🎯 Skill Coverage Analysis**")
    full_resume_lower = results['full_resume'].lower()
    role_skills = results.get('role_data', {}).get('skills', [])
    
    # Proper Categorization
    categories = {
        "Programming": ["python", "java", "c++", "c#", "javascript", "typescript", "ruby", "go", "php", "r", "swift", "kotlin", "html", "css", "django", "react", "nodejs"],
        "ML/AI": ["machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy", "llm", "transformers", "opencv", "yolo", "reinforcement learning"],
        "Tools": ["docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "jenkins", "jira", "terraform", "linux", "cloud", "api", "rest"],
        "Data": ["sql", "mysql", "mongodb", "postgres", "spark", "hadoop", "oracle", "nosql", "redis", "excel", "tableau", "power bi", "database"]
    }
    
    found_skills = set()
    category_scores = {k: 0 for k in categories}
    
    # Check all categorised keywords AND explicitly injected role_skills
    all_keywords_to_check = set(role_skills)
    for cat, items in categories.items():
        all_keywords_to_check.update(items)
        
    # Extraction & deduplication
    for kw in all_keywords_to_check:
        if kw.lower() in full_resume_lower:
            found_skills.add(kw.lower())
            
    # Compute proportional categorical strength
    for cat, items in categories.items():
        found_in_cat = [i for i in items if i in found_skills]
        # Multiplier depends loosely on core expected broad skills
        score = min(100, len(found_in_cat) * 25)
        category_scores[cat] = score
        
    # Overall Score Computation
    skill_strength = min(100, len(found_skills) * 10)
    
    # UI Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.success(f"✅ **Extracted Skills** ({len(found_skills)})")
        if found_skills:
            st.info(" • ".join([s.title() for s in sorted(list(found_skills))[:18]]))
        else:
            st.info("No matching skills found")
            
    with col2:
        st.success(f"💪 **Overall Skill Strength**")
        st.progress(skill_strength / 100.0, text=f"{skill_strength}% Strength Score")
        st.markdown("---")
        for cat, score in category_scores.items():
            st.markdown(f"**{cat}** → {score}%")
            st.progress(score / 100.0)

def comprehensive_resume_review(resume_text):
    """Analyze resume across multiple dimensions for overall review"""
    
    # Basic structure analysis
    sections_found = []
    sections = ["experience", "education", "skills", "projects", "summary", "objective"]
    text_lower = resume_text.lower()
    
    for section in sections:
        if section in text_lower:
            sections_found.append(section.title())
    
    # Contact info detection
    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+', text_lower))
    has_phone = bool(re.search(r'\d{10,}', text_lower))
    
    # Action verbs detection
    action_verbs = ["developed", "designed", "implemented", "created", "led", "managed", "built", "deployed"]
    action_verbs_count = sum(1 for verb in action_verbs if verb in text_lower)
    
    # Quantifiable achievements
    has_quant = bool(re.search(r'\d+%|\d+x|\d+\s*(?:years?|months?)|saved\s+\$?\d+|increased\s+\d+', text_lower))
    
    # Length analysis
    word_count = len(resume_text.split())
    length_status = "Ideal (150-400 words)" if 150 <= word_count <= 400 else "Review Length" if word_count < 150 else "Too Long"
    
    # Tech stack detection
    tech_stack = []
    tech_terms = {
        "python": ["python"],
        "ml": ["machine learning", "tensorflow", "pytorch", "scikit-learn"],
        "web": ["react", "javascript", "html", "css", "nodejs"],
        "cloud": ["aws", "azure", "gcp"],
        "devops": ["docker", "kubernetes", "jenkins"],
        "database": ["sql", "mongodb", "postgres", "mysql"]
    }
    
    for category, terms in tech_terms.items():
        if any(term in text_lower for term in terms):
            tech_stack.append(category.title())
    
    # Grammar/Professionalism indicators
    has_github = "github" in text_lower
    has_portfolio = any(x in text_lower for x in ["portfolio", "personal website", "linkedin"])
    
    return {
        "sections_found": sections_found,
        "has_contact": has_email and has_phone,
        "action_verbs": action_verbs_count,
        "has_quant": has_quant,
        "word_count": word_count,
        "length_status": length_status,
        "tech_stack": tech_stack,
        "has_github": has_github,
        "has_portfolio": has_portfolio
    }

def extract_experience_years(resume_text):
    if not resume_text:
        return 0
    text_lower = resume_text.lower()
    patterns = [
        r'(\d+)\s*(?:years?|yrs?|y\.?|years?\s+of\s+exp(?:erience)?)',  
        r'(\d+)\s*year(?:s?)?\s*(?:exp|experience)?',  
        r'experience[:\-]?\s*(\d+)',  
        r'(\d+)\s*\+\s*(?:years?|yrs?)',  
        r'(\d+)\s*years?',  
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    return 0

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  
        u"\U0001F300-\U0001F5FF"  
        u"\U0001F680-\U0001F6FF"  
        u"\U0001F1E0-\U0001F1FF"  
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()

def clean_resume(text):
    if not isinstance(text, str):
        return ""
    text = re.sub('http\S+\s*', ' ', text)
    text = re.sub('RT|cc', ' ', text)
    text = re.sub('#\S+', '', text)
    text = re.sub('@\S+', '  ', text)
    text = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', text)
    text = re.sub(r'[^\x00-\x7f]',r' ', text) 
    text = re.sub('\s+', ' ', text)
    return text.lower().strip()

@st.cache_resource
def load_ml_models():
    if os.path.exists('ml_models/best_model.pkl') and os.path.exists('ml_models/tfidf_vectorizer.pkl') and os.path.exists('ml_models/label_encoder.pkl'):
        model = joblib.load('ml_models/best_model.pkl')
        vectorizer = joblib.load('ml_models/tfidf_vectorizer.pkl')
        le = joblib.load('ml_models/label_encoder.pkl')
        return model, vectorizer, le
    return None, None, None

@st.cache_data
def predict_role_from_model(resume_text):
    model, vectorizer, le = load_ml_models()
    if model and vectorizer and le:
        cleaned = clean_resume(resume_text)
        features = vectorizer.transform([cleaned]).toarray()
        
        probs = model.predict_proba(features)[0]
        
        top3_indices = probs.argsort()[-3:][::-1]
        top3_roles = le.inverse_transform(top3_indices)
        top3_probs = probs[top3_indices]
        
        prediction = top3_roles[0]
        confidence = top3_probs[0] * 100
        
        return prediction, confidence, list(zip(top3_roles, top3_probs))
    return None, 0.0, []

@st.cache_data
def get_all_job_roles():
    pdf_safe_roles = {
        "ML Engineer": {"skills": ["machine learning", "tensorflow", "pytorch", "scikit-learn", "python", "nlp", "computer vision"], "exp": 3, "color": "#000000"},
        "Data Scientist": {"skills": ["machine learning", "statistics", "python", "deep learning", "sql", "feature engineering"], "exp": 4, "color": "#18181b"},
        "AI Research Scientist": {"skills": ["deep learning", "transformers", "research", "publications", "llm", "reinforcement learning"], "exp": 5, "color": "#27272a"},
        "MLOps Engineer": {"skills": ["mlflow", "kubeflow", "sagemaker", "docker", "kubernetes", "model deployment"], "exp": 3, "color": "#3f3f46"},
        "Computer Vision Engineer": {"skills": ["opencv", "yolo", "tensorrt", "image processing", "object detection"], "exp": 3, "color": "#52525b"},
        "NLP Engineer": {"skills": ["bert", "transformers", "spacy", "llm", "sentiment analysis", "ner"], "exp": 3, "color": "#71717a"},
        "Data Analyst": {"skills": ["sql", "python", "pandas", "machine learning", "power bi", "tableau"], "exp": 2, "color": "#a1a1aa"},
        "Data Engineer": {"skills": ["spark", "hadoop", "airflow", "kafka", "feature store", "ml pipelines"], "exp": 4, "color": "#d4d4d8"},
        "Full Stack Developer": {"skills": ["react", "nodejs", "python", "django", "mongodb", "docker"], "exp": 3, "color": "#18181b"},
        "DevOps Engineer": {"skills": ["kubernetes", "docker", "jenkins", "terraform", "aws", "mlops"], "exp": 4, "color": "#27272a"},
        "Frontend Developer": {"skills": ["react", "javascript", "html", "css", "vue", "angular"], "exp": 2, "color": "#3f3f46"},
        "Backend Developer": {"skills": ["python", "django", "flask", "nodejs", "sql", "api"], "exp": 3, "color": "#52525b"},
        "Python Developer": {"skills": ["python", "django", "flask", "pandas", "fastapi", "sqlalchemy"], "exp": 2, "color": "#71717a"},
        "Java Developer": {"skills": ["java", "spring", "hibernate", "maven", "microservices"], "exp": 3, "color": "#a1a1aa"},
        "Software Engineer": {"skills": ["java", "python", "c++", "algorithms", "data structures"], "exp": 3, "color": "#d4d4d8"},
        "Business Analyst": {"skills": ["sql", "excel", "requirements", "jira", "agile", "stakeholder"], "exp": 3, "color": "#18181b"},
        "Product Manager": {"skills": ["agile", "jira", "product roadmap", "stakeholder", "user stories"], "exp": 4, "color": "#27272a"},
        "Project Manager": {"skills": ["pmp", "agile", "scrum", "jira", "risk management"], "exp": 5, "color": "#3f3f46"},
        "QA Engineer": {"skills": ["selenium", "pytest", "jira", "test cases", "automation"], "exp": 2, "color": "#52525b"},
        "Cybersecurity Analyst": {"skills": ["firewall", "siem", "penetration testing", "vulnerability"], "exp": 3, "color": "#71717a"},
        "Cloud Engineer": {"skills": ["aws", "azure", "gcp", "terraform", "docker"], "exp": 3, "color": "#a1a1aa"},
        "Blockchain Developer": {"skills": ["solidity", "ethereum", "smart contracts", "web3"], "exp": 2, "color": "#d4d4d8"},
        "Mobile Developer": {"skills": ["flutter", "react native", "swift", "kotlin"], "exp": 2, "color": "#18181b"},
        "iOS Developer": {"skills": ["swift", "swiftui", "xcode", "core data"], "exp": 2, "color": "#27272a"},
        "Android Developer": {"skills": ["kotlin", "java", "android studio", "jetpack"], "exp": 2, "color": "#3f3f46"}
    }
    
    ui_roles = {f"🤖 {k}" if "ML" in k or "AI" in k else f"🔬 {k}" if "Data" in k else f"💻 {k}": v for k, v in pdf_safe_roles.items()}
    ui_roles.update({
        "👁️ Computer Vision Engineer": pdf_safe_roles["Computer Vision Engineer"],
        "🗣️ NLP Engineer": pdf_safe_roles["NLP Engineer"],
        "⚙️ Data Engineer": pdf_safe_roles["Data Engineer"],
        "📊 Data Analyst": pdf_safe_roles["Data Analyst"]
    })
    return ui_roles, pdf_safe_roles

@st.cache_data
def extract_text(file):
    try:
        content = file.read()
        file.seek(0)
        if file.name.lower().endswith('.pdf'):
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            return text.strip()
        elif file.name.lower().endswith('.docx'):
            doc = Document(io.BytesIO(content))
            return " ".join([para.text for para in doc.paragraphs if para.text.strip()])
        elif file.name.lower().endswith('.txt'):
            return content.decode('utf-8')
        return ""
    except:
        return ""

@st.cache_data
def ml_resume_classifier(resume_text):
    if not resume_text: return 0
    ml_keywords = ["machine learning", "deep learning", "neural network", "tensorflow", "pytorch","scikit-learn", "nlp", "computer vision", "transformers", "gradient boosting","feature engineering", "model deployment", "hyperparameter", "cross validation","random forest", "xgboost", "llm", "bert", "yolo", "opencv"]
    score = 0
    text_lower = resume_text.lower()
    for keyword in ml_keywords:
        if keyword in text_lower:
            score += 8
    return min(score, 100)

@st.cache_data
def advanced_ml_similarity(resume_text, job_skills):
    try:
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        resume_doc = [resume_text.lower()]
        job_doc = [' '.join(job_skills).lower()]
        tfidf_matrix = vectorizer.fit_transform(resume_doc + job_doc)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity * 100
    except:
        return 0

@st.cache_data
def advanced_ats_score(text):
    if not text: return 0
    score = 0
    text_lower = text.lower()
    sections = ["experience", "education", "skills", "projects"]
    score += sum(20 for sec in sections if sec in text_lower)
    if re.search(r'[\w\.-]+@[\w\.-]+', text_lower): score += 15
    if re.search(r'\d{10,}', text_lower): score += 10
    verbs = ["developed", "designed", "implemented", "created", "led"]
    score += sum(5 for verb in verbs if verb in text_lower)
    tech_terms = ["github", "aws", "docker", "api", "database"]
    score += sum(3 for term in tech_terms if term in text_lower)
    return min(score, 100)

def skill_match_score(resume_text, job_skills):
    resume_words = set(re.sub(r'[^ \w\s]', '', resume_text.lower()).split())
    job_words = set(job_skills)
    matched = len(resume_words.intersection(job_words))
    total = len(job_words)
    return (matched / total * 100) if total > 0 else 0

def get_role_fit_reason(score):
    if score > 85: return "Excellent: Perfect semantic alignment with role requirements using TF-IDF + ML keyword matching"
    elif score > 70: return "Strong: High similarity (70%+) with core role competencies detected"
    elif score > 50: return "Good: Moderate match - develop 2-3 key skills for perfect fit"
    else: return "Develop: Foundational skills detected - focus on role-specific ML frameworks"

def get_top_role_reason(role_name, score, resume_text, all_roles):
    if role_name not in all_roles:
        return f"Score: {int(score)}% - Great foundational match"
    
    role_skills = all_roles[role_name]['skills']
    resume_words = set(re.sub(r'[^ \w\s]', '', resume_text.lower()).split())
    matched_skills = [skill for skill in role_skills if skill.lower() in resume_words]
    
    if score > 85:
        reason = f"🎯 {len(matched_skills)}/{len(role_skills)} core skills match"
    elif score > 70:
        reason = f"✅ Strong match on {len(matched_skills)} key skills"
    elif score > 50:
        reason = f"🔄 {len(matched_skills)} transferable skills found"
    else:
        reason = f"📈 Build on {len(matched_skills)} matching skills"
    
    return f"{reason} ({int(score)}%)"

# 🔥 FIXED: No more duplicate roles!
@st.cache_data
def find_best_roles(resume_text):
    """Enhanced version - Returns UNIQUE top 5 roles with diverse scoring"""
    _, pdf_safe_roles = get_all_job_roles()
    scores = {}
    
    for role, data in pdf_safe_roles.items():
        # Enhanced scoring with diversity
        skill_score = skill_match_score(resume_text, data['skills'])
        
        # Add ML relevance boost for ML roles
        ml_boost = 15 if any(ml_keyword in resume_text.lower() 
                           for ml_keyword in ["machine learning", "deep learning", "nlp", "computer vision"]) else 0
        
        # Role category diversity scoring
        role_type_score = 0
        if "ML" in role or "AI" in role:
            role_type_score = ml_resume_classifier(resume_text) * 0.2
        elif "Data" in role:
            role_type_score = 40 if "sql" in resume_text.lower() or "pandas" in resume_text.lower() else 20
        elif "Dev" in role or "Developer" in role:
            role_type_score = 30 if "python" in resume_text.lower() or "javascript" in resume_text.lower() else 10
        
        # Combined diverse score
        role_score = skill_score * 0.6 + ml_boost * 0.2 + role_type_score * 0.2
        scores[role] = role_score
    
    # Get TOP 5 UNIQUE roles (already unique by construction)
    sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_roles[:5]

def get_ml_score_reason(score):
    if score > 70: return "Production-Ready: Advanced ML frameworks (PyTorch/TensorFlow) + modern techniques detected"
    elif score > 50: return "Intermediate: Solid ML foundation with scikit-learn + basic deep learning"
    elif score > 30: return "Beginner+: ML fundamentals present - build deployment/production skills"
    else: return "Entry-Level: Add ML projects + frameworks to reach production readiness"

def get_similarity_reason(score):
    if score > 80: return "Perfect Match: Exact skillset overlap with role requirements"
    elif score > 60: return "Strong Overlap: 60%+ core skills match detected via cosine similarity"
    elif score > 40: return "Partial Match: Key transferable skills identified"
    else: return "Gap Analysis: Target 4-5 role-specific skills from job profile"

def get_ats_reason(score):
    if score > 85: return "ATS-Optimized: Perfect keyword density + structured format"
    elif score > 70: return "ATS-Friendly: Strong structure + required sections detected"
    elif score > 50: return "ATS-Compatible: Basic optimization - add quantifiable achievements"
    else: return "Improve: Add sections (Experience/Skills/Projects) + keywords"

def get_experience_reason(years, required_exp):
    if years >= required_exp + 1: return f"Senior-Level: {years} yrs exceeds {required_exp} yrs requirement"
    elif years >= required_exp: return f"Perfect Fit: {years} yrs matches exact experience requirement"
    elif years >= required_exp - 1: return f"Near Match: {years} yrs (1 yr short) - strong potential"
    else: return f"Grow: {years} yrs - gain {required_exp-years} yrs hands-on experience"

def create_radar_chart(role_fit, ats_score, skill_score, ml_score):
    categories = ['Role Fit', 'ATS Score', 'Skills', 'ML Score']
    values = [role_fit, ats_score, skill_score, ml_score]
    values += values[:1]
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    ax.plot(angles, values, 'o-', linewidth=4, label='Your Score', color='#10b981', markersize=12, markerfacecolor='white', markeredgewidth=2)
    ax.fill(angles, values, color='#10b981', alpha=0.15)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold', color='#1e293b')
    for i, (angle, value) in enumerate(zip(angles[:-1], values[:-1])):
        ax.text(angle, value + 3, f'{int(value)}%', ha='center', va='center', fontsize=10, fontweight='bold', color='#1e3a8a')
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=10, color='#64748b')
    ax.grid(True, color='#e5e7eb', linewidth=1, alpha=0.8)
    ax.set_title('ML Competency Scorecard', size=16, fontweight='bold', pad=30, color='#1e293b')
    ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1.0), fontsize=10)
    plt.tight_layout()
    return fig

def safe_text(text):
    """Ensure text is latin-1 compatible for FPDF to prevent UnicodeEncodeError"""
    if not isinstance(text, str):
        return ""
    # Use existing remove_emojis to clean known emoji blocks first
    no_emojis = remove_emojis(text)
    # Force latin-1 compatibility
    return no_emojis.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(results, role_data):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 18)
            self.set_fill_color(30, 58, 138)
            self.set_text_color(255, 255, 255)
            self.cell(0, 15, safe_text('  Candidate Evaluation Report - AI Talent Scout Pro'), 0, 1, 'L', fill=True)
            self.ln(5)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, safe_text(f'Confidential Report | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Powered by AI'), 0, 0, 'C')
    
    pdf = PDF()
    pdf.add_page()
    
    def section_header(title):
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(16, 185, 129)
        pdf.cell(0, 10, safe_text(f'  {title}'), 0, 1, 'L', fill=True)
        pdf.ln(3)

    # Prepare data
    full_resume = results.get('full_resume', '')
    rev_data = comprehensive_resume_review(full_resume)
    full_lower = full_resume.lower()
    role_skills = role_data.get('skills', [])
    found_skills = [s for s in role_skills if s.lower() in full_lower]
    missing_skills = [s for s in role_skills if s.lower() not in full_lower]

    clean_role = safe_text(results.get("role", "Unknown Role"))
    hire_prob = min(95, results['role_fit'] + results['ml_score'] * 0.5)
    decision = "EXCELLENT - HIRE" if hire_prob > 85 else "STRONG - INTERVIEW" if hire_prob > 70 else "GOOD - DEVELOP"

    # --- 1. OVERALL SUMMARY ---
    section_header('1. OVERALL SUMMARY')
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 8, safe_text('Role Analyzed:'), 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, safe_text(clean_role), 0, 1)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(40, 8, safe_text('Recommendation:'), 0, 0)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 8, safe_text(decision), 0, 1)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(40, 8, safe_text('Hire Probability:'), 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, safe_text(f"{int(hire_prob)}% likelihood of success in role"), 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'I', 11)
    pdf.set_text_color(80, 80, 80)
    summary_text = f"Candidate shows a {int(hire_prob)}% overall alignment for the {clean_role} position, driven by their existing technical skills and ML model evaluations. See explicit breakdown below."
    pdf.multi_cell(0, 6, safe_text(summary_text))
    pdf.ln(5)

    # --- 2. SCORE BREAKDOWN ---
    section_header('2. SCORE BREAKDOWN & METRICS')
    metrics = [
        ("Role Fit", f"{int(results['role_fit'])}%", get_role_fit_reason(results['role_fit']), "Indicates how well candidate matches job requirements."),
        ("ML Score", f"{int(results['ml_score'])}/100", get_ml_score_reason(results['ml_score']), "Shows technical depth in machine learning."),
        ("Skill Similarity", f"{int(results['skill_similarity'])}%", get_similarity_reason(results['skill_similarity']), "Measures alignment with required skills."),
        ("ATS Score", f"{int(results['ats_score'])}/100", get_ats_reason(results['ats_score']), "Determines resume visibility in hiring systems."),
        ("Experience", f"{results['experience']} yrs", get_experience_reason(results['experience'], role_data.get('exp', 3)), "Reflects practical exposure and readiness.")
    ]
    
    for title, score, reason, importance in metrics:
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 6, safe_text(f'{title}:'), 0, 0)
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(16, 185, 129)
        pdf.cell(0, 6, safe_text(score), 0, 1)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(10)
        pdf.multi_cell(0, 5, safe_text(f"Reason: {reason}"))
        
        pdf.set_text_color(100, 100, 100)
        pdf.cell(10)
        pdf.multi_cell(0, 5, safe_text(f"Importance: {importance}"))
        pdf.ln(3)

    # --- 3. STRENGTHS ---
    section_header('3. HIGHLIGHTED STRENGTHS')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    strengths = []
    if found_skills:
        strengths.append(f"Top matching technical skills: {', '.join([s.title() for s in found_skills[:6]])}")
    if rev_data["action_verbs"] >= 4:
        strengths.append("Excellent communication demonstrated by strong action verbs (indicates leadership).")
    if rev_data["has_quant"]:
        strengths.append("High business impact proven through quantifiable achievements and metrics.")
    if results['ats_score'] >= 75:
        strengths.append("Resume formatting is highly ATS-compliant and industry standard.")
    if len(strengths) == 0:
        strengths.append("Demonstrates foundational understanding capable of fulfilling entry requirements.")
    for s in strengths:
        pdf.multi_cell(0, 6, safe_text(f"[*] {s}"))
    pdf.ln(5)

    # --- 4. IMPROVEMENT AREAS ---
    section_header('4. IMPROVEMENT AREAS')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    improvements = []
    if missing_skills:
        improvements.append(f"Technical Gap: Candidate lacks explicitly stated core skills like {', '.join([s.title() for s in missing_skills[:4]])}.")
    if rev_data["action_verbs"] < 3:
        improvements.append("Action Items: Use stronger declarative verbs to show ownership of past projects.")
    if not rev_data["has_quant"]:
        improvements.append("Impact Measurement: Missing quantifiable metrics (e.g., increased performance by 20%).")
    if results['ats_score'] < 60:
        improvements.append("Formatting: Resume lacks clear standard sections making it harder for ATS parsing.")
    if len(improvements) == 0:
        improvements.append("Resume is robustly optimized. No critical improvements needed.")
    for imp in improvements:
        pdf.multi_cell(0, 6, safe_text(f"[!] {imp}"))
    pdf.ln(5)

    # --- 5. TOP ROLE RECOMMENDATIONS ---
    section_header('5. TOP ROLE RECOMMENDATIONS')
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    for i, (role, score) in enumerate(results.get('top_roles', [])[:3], 1):
        clean_name = safe_text(role)
        logic = "Exceptional alignment with candidate trajectory." if score > 75 else "Good transferable skill overlap."
        pdf.cell(10)
        pdf.multi_cell(0, 6, safe_text(f"{i}. {clean_name} ({int(score)}%) - {logic}"))
    pdf.ln(5)

    # --- 6. FINAL VERDICT ---
    section_header('6. FINAL VERDICT')
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, safe_text(f"Action: {decision}"), 0, 1)
    pdf.set_font('Arial', '', 11)
    if hire_prob > 85:
        verdict = "The candidate is a highly viable asset. Their technical score overlaps heavily with core job requirements and they possess significant practical indicators. Proceed to technical assessment."
    elif hire_prob > 70:
        verdict = "The candidate is a strong fit. They meet the majority of technical requirements but may require mild onboarding or skill verification. Recommend setting up an initial interview."
    else:
        verdict = "The candidate does not currently meet the rigorous threshold for immediate senior placement in this role. Recommend considering for junior roles or re-evaluating after gap closure."
    pdf.multi_cell(0, 6, safe_text(verdict))

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes

# MAIN UI - ENHANCED WITH RESUME REVIEW
st.set_page_config(
    page_title="🤖 AI Talent Scout Pro - ML Powered",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SaaS Theme Engine Implementation
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "Dark"

def apply_theme(theme_name):
    themes = {
        "Light": {
            "bg": "#ffffff",
            "text": "#000000",
            "card_bg": "rgba(255,255,255,0.95)",
            "header_gradient": "linear-gradient(90deg, #000000 0%, #71717a 100%)",
            "metric_grad": "linear-gradient(135deg, #000000 0%, #3f3f46 100%)",
            "shadow": "rgba(0,0,0,0.1)"
        },
        "Dark": {
            "bg": "#000000",
            "text": "#ffffff",
            "card_bg": "rgba(24,24,27,0.95)",
            "header_gradient": "linear-gradient(90deg, #ffffff 0%, #a1a1aa 100%)",
            "metric_grad": "linear-gradient(135deg, #18181b 0%, #000000 100%)",
            "shadow": "rgba(0,0,0,0.8)"
        }
    }
    t = themes.get(theme_name, themes["Dark"])
    
    st.markdown(f"""
    <style>
        /* 1. Force Streamlit Root Targets to adopt Theme Colors */
        .stApp, [data-testid="stAppViewContainer"] {{
            background-color: {t['bg']} !important;
            transition: background-color 0.5s ease;
        }}
        [data-testid="stSidebar"] {{
            background-color: {t['card_bg']} !important;
        }}
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        
        /* 2. Global Text Color Override - Use safely across the DOM */
        .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp li, .stMarkdown p {{
            color: {t['text']} !important;
        }}
        
        /* 3. Force Explicit Components to Stay their Designed Color */
        .metric-card p, .metric-card h1, .metric-card h2, .metric-card h3, .metric-title, .ml-badge {{
            color: white !important;
        }}
        
        /* 4. Guaranteed Solid Visible Main Header */
        h1.main-header, .main-header {{
            font-size: 3.5rem !important;
            font-weight: 900 !important;
            color: {'#ffffff' if theme_name == 'Dark' else '#1e293b'} !important; 
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 0px 4px 15px {t['shadow']};
            transition: color 0.3s ease;
        }}
        .metric-card {{
            background: {t['metric_grad']};
            padding: 1.5rem;
            border-radius: 20px;
            color: white !important;
            box-shadow: 0 10px 30px {t['shadow']};
            margin-bottom: 1.5rem;
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 35px {t['shadow']};
        }}
        .ml-badge {{
            background: {t['header_gradient']};
            color: white !important;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: bold;
            font-size: 0.9rem;
            display: inline-block;
            margin: 0.5rem 0;
            box-shadow: 0 4px 10px {t['shadow']};
            border: none;
        }}
        .pro-header {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {t['text']} !important;
            margin-bottom: 1rem;
        }}
        .reason-card {{
            background: {t['card_bg']};
            padding: 1.5rem;
            border-radius: 20px;
            border-left: 6px solid #10b981;
            box-shadow: 0 4px 12px {t['shadow']};
            height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            font-size: 0.9rem;
            line-height: 1.5;
            color: {t['text']} !important;
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        .reason-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 6px 16px {t['shadow']};
        }}
        .excellent {{ border-left-color: #10b981 !important; }}
        .good {{ border-left-color: #f59e0b !important; }}
        .average {{ border-left-color: #eab308 !important; }}
        .needs-work {{ border-left-color: #ef4444 !important; }}
        .metric-title {{
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            margin: 0 0 0.5rem 0 !important;
            color: white !important;
        }}
        .role-leaderboard-card {{
            background: {t['card_bg']};
            padding: 1.2rem;
            border-radius: 16px;
            border-left: 5px solid #10b981;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 8px {t['shadow']};
            transition: all 0.3s ease;
            height: 90px;
            display: flex;
            align-items: center;
            cursor: pointer;
            color: {t['text']} !important;
        }}
        .role-leaderboard-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px {t['shadow']};
            border-left-color: #059669 !important;
        }}
        .role-name {{
            font-weight: 700;
            font-size: 1.1rem;
            flex: 1;
            color: {t['text']} !important;
        }}
        .role-score {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #10b981 !important;
            margin-right: 1rem;
        }}
        .role-reason {{
            font-size: 0.85rem;
            opacity: 0.8;
            line-height: 1.4;
            max-height: 40px;
            overflow: hidden;
            color: {t['text']} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme(st.session_state.ui_theme)

# MAIN UI LOGIC
st.markdown('<h1 class="main-header">🤖 AI Talent Scout Pro</h1>', unsafe_allow_html=True)
st.markdown('<div class="ml-badge">🚀 Powered by TF-IDF + Machine Learning Models</div>', unsafe_allow_html=True)
st.markdown("---")

with st.sidebar:
    st.header("🎨 **Appearance**")
    theme_choice = st.selectbox("UI Theme", ["Light", "Dark"], index=["Light", "Dark"].index(st.session_state.ui_theme))
    if theme_choice != st.session_state.ui_theme:
        st.session_state.ui_theme = theme_choice
        st.rerun()
    st.markdown("---")
    
    app_mode = st.radio("Navigation", ["🔍 Analyze Resume", "⚙️ ML Training Studio"])
    
if app_mode == "⚙️ ML Training Studio":
    st.markdown('<h2 class="pro-header">⚙️ ML Training Studio</h2>', unsafe_allow_html=True)
    st.info("🚀 **Advanced Trainer:** Upload any Kaggle or custom resume dataset. We automatically map columns and validate data quality before training.")
    
    dataset_file = st.file_uploader("Upload CSV Dataset (Kaggle formats supported)", type=['csv'])
    if dataset_file:
        df = pd.read_csv(dataset_file)
        
        # 🟢 1. Flexible Column Mapping (Automatically detect columns)
        resume_cols = ['Resume', 'resume', 'Resume_str', 'resume_text', 'text', 'cv_text', 'Resume_text', 'RESUME']
        category_cols = ['Category', 'category', 'Label', 'label', 'Role', 'role', 'Job_Category', 'JOB_ROLE', 'CLASS']
        
        found_resume_col = next((col for col in df.columns if col in resume_cols), None)
        found_category_col = next((col for col in df.columns if col in category_cols), None)
        
        if not found_resume_col or not found_category_col:
            st.error("❌ **Dataset structure incompatible!**")
            st.warning(f"Expected Resume column (detected: {found_resume_col}) and Category column (detected: {found_category_col}).")
            st.info("💡 **Corrective Action:** Ensure your CSV has columns like 'Resume' and 'Category' (or common variants).")
            st.stop()
            
        df = df.rename(columns={found_resume_col: 'Resume', found_category_col: 'Category'})
        
        # 🟢 2. Data Cleaning
        initial_len = len(df)
        df = df.dropna(subset=['Resume', 'Category']) # Remove missing
        df['Category'] = df['Category'].astype(str).str.strip() # Clean categories
        df = df[df['Resume'].astype(str).str.strip() != ""] # Remove empty resumes
        df = df.drop_duplicates(subset=['Resume']) # Remove duplicates
        cleaned_len = len(df)
        
        # 🟢 3. Training Dashboard / Stats
        st.markdown("### 📊 **Dataset Quality Report**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Valid Resumes", cleaned_len, delta=f"{cleaned_len - initial_len} rows cleaned")
        unique_cats = df['Category'].nunique()
        c2.metric("Total Categories", unique_cats)
        
        # Category distribution
        counts = df['Category'].value_counts()
        
        # Validations
        val_errors = []
        if unique_cats < 2:
            val_errors.append("The dataset contains only one category. Supervised training requires at least **2 unique categories**.")
        
        min_samples = counts.min()
        if min_samples < 2:
            val_errors.append(f"Category **'{counts.idxmin()}'** has only {min_samples} sample(s). All categories must have **at least 2 samples** for stratified training.")

        if val_errors:
            for err in val_errors:
                st.error(f"🚫 {err}")
            st.warning("⚠️ **Corrective Action:** Please upload a more balanced dataset with multiple categories and at least 2 samples per role.")
        
        # Display Preview & Distribution
        with st.expander("👁️ View Data Preview"):
            st.dataframe(df.head(5), use_container_width=True)
            
        # Plot Distribution
        fig_dist, ax_dist = plt.subplots(figsize=(10, 6))
        sns.barplot(x=counts.values, y=counts.index, palette="viridis", ax=ax_dist)
        ax_dist.set_title("Resume Distribution per Category")
        ax_dist.set_xlabel("Count")
        st.pyplot(fig_dist)
        
        # Imbalance warning
        if unique_cats > 1:
            imbalance_ratio = counts.max() / counts.min()
            if imbalance_ratio > 4:
                st.warning(f"⚖️ **Class Imbalance Warning:** The largest category is {imbalance_ratio:.1f}x larger than the smallest. The model might favor frequent classes.")

        if not val_errors:
            st.markdown("---")
            if st.button("🚀 **START PRODUCTION TRAINING**", type="primary", use_container_width=True):
                with st.spinner("🤖 Training Ensemble (Logistic Regression, Random Forest, SVM)..."):
                    # Preprocessing
                    df['cleaned'] = df['Resume'].apply(clean_resume)
                    le = LabelEncoder()
                    y = le.fit_transform(df['Category'])
                    
                    tfidf = TfidfVectorizer(sublinear_tf=True, stop_words='english', max_features=2500)
                    X = tfidf.fit_transform(df['cleaned']).toarray()
                    
                    # Stratified Split
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
                    
                    models = {
                        "Logistic Regression": LogisticRegression(max_iter=2000, multi_class='ovr', C=1.0),
                        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
                        "Support Vector Machine": SVC(kernel='linear', probability=True, C=1.0)
                    }
                    
                    best_acc = 0.0
                    best_model = None
                    best_name = ""
                    metrics_results = []
                    
                    progress_bar = st.progress(0, text="Comparing models...")
                    for idx, (name, model) in enumerate(models.items()):
                        progress_bar.progress((idx + 1) / len(models), text=f"Evaluating {name}...")
                        model.fit(X_train, y_train)
                        y_pred = model.predict(X_test)
                        
                        acc = accuracy_score(y_test, y_pred)
                        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                        
                        metrics_results.append({
                            "Model": name, 
                            "Accuracy": f"{acc*100:.2f}%", 
                            "Precision": f"{prec*100:.2f}%", 
                            "Recall": f"{rec*100:.2f}%", 
                            "F1": f"{f1*100:.2f}%"
                        })
                        
                        if acc > best_acc:
                            best_acc = acc
                            best_model = model
                            best_name = name
                    
                    st.success(f"🏆 **Winner: {best_name}** ({best_acc*100:.2f}% Accuracy)")
                    st.table(pd.DataFrame(metrics_results))
                    
                    # Persistence
                    os.makedirs('ml_models', exist_ok=True)
                    joblib.dump(best_model, 'ml_models/best_model.pkl')
                    joblib.dump(tfidf, 'ml_models/tfidf_vectorizer.pkl')
                    joblib.dump(le, 'ml_models/label_encoder.pkl')
                    
                    # Performance visualization
                    y_pred_best = best_model.predict(X_test)
                    cm = confusion_matrix(y_test, y_pred_best)
                    fig_cm, ax_cm = plt.subplots(figsize=(12, 10))
                    sns.heatmap(cm, annot=False, cmap='Greens', xticklabels=le.classes_, yticklabels=le.classes_)
                    plt.title(f"Confusion Matrix: {best_name}")
                    plt.xticks(rotation=90)
                    st.pyplot(fig_cm)
                    
                    st.balloons()
                    st.success("✅ **Production Model Deployed!** Future analyses will use this state-of-the-art model.")
    st.stop()


with st.sidebar:
    st.header("📁 **Upload Resume**")
    analysis_mode = st.radio("Mode", ["Single", "Multiple"])
    
    if analysis_mode == "Single":
        resume_file = st.file_uploader("Choose PDF/DOCX/TXT", type=['pdf','docx','txt'])
        resume_files = []
    else:
        resume_files = st.file_uploader("Choose Multiple PDF/DOCX/TXT", type=['pdf','docx','txt'], accept_multiple_files=True)
        resume_file = None
    
    st.header("🎯 **ML Role Analysis**")
    ui_roles, _ = get_all_job_roles()
    
    if analysis_mode == "Single":
        selected_role = st.selectbox("**Select Target Role**", list(ui_roles.keys()), index=0)
    else:
        st.info("🤖 **Automatic ML Role Detection** (Multiple Mode)")
        selected_role = None  # Handled per resume
        
    st.markdown("---")
    detailed_view = st.checkbox("🔬 **ML Detailed Analysis**", value=True)
    fast_mode = st.checkbox("⚡ **Fast Mode (Skip heavy TF-IDF)**", value=False)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<h2 class="pro-header">🎓 ML-Powered Resume Analysis</h2>', unsafe_allow_html=True)
    
    if 'results' in st.session_state and st.session_state.results.get('success'):
        if st.session_state.results.get('mode') == 'Single':
            pred_role = st.session_state.results.get('predicted_role', 'Unknown Role')
            conf = st.session_state.results.get('model_confidence', 0.0)
            
            st.markdown(f"""
            <div style="padding: 1.2rem; border-radius: 12px; background: rgba(16, 185, 129, 0.1); border-left: 6px solid #10b981; margin-bottom: 1rem;">
                <h3 style="margin:0; color: #10b981; font-weight: 800;">🎯 Target Role: {pred_role}</h3>
                <p style="margin:5px 0 0 0; opacity: 0.9;"><strong>ML Confidence:</strong> {conf*100:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            top3 = st.session_state.results.get('top3_preds', [])
            if top3:
                scols = st.columns(3)
                for idx, (r, p) in enumerate(top3[:3]):
                    with scols[idx]:
                        st.info(f"**Alt #{idx+1}: {r}**\n\n*(Match: {p*100:.1f}%)*")
        else:
            multi_res = st.session_state.get('multi_results', [])
            st.success(f"🎯 **Batch Analysis Complete:** Autonomously processed {len(multi_res)} candidate resumes.")
    else:
        st.warning("⚠️ **No analysis yet. Please upload a resume and click RUN COMPLETE ML ANALYSIS.**")

with col2:
    st.markdown('<h2 class="pro-header">🚀 ML Analyze</h2>', unsafe_allow_html=True)
    if st.button("🔥 **🤖 RUN COMPLETE ML ANALYSIS**", type="primary", use_container_width=True):
        if analysis_mode == "Single" and resume_file is None:
            st.error("❌ **Upload resume first!**")
        elif analysis_mode == "Multiple" and not resume_files:
            st.error("❌ **Upload at least one resume first!**")
        else:
            with st.spinner("🤖 ML Models Processing..."):
                ui_roles, pdf_safe_roles = get_all_job_roles()
                
                # MODIFIED CODE: Handle Single OR Multiple Mode
                if analysis_mode == "Single":
                    pdf_role_name = next(k for k, v in pdf_safe_roles.items() if selected_role.replace('🤖','').replace('🔬','').replace('💻','').replace('👁️','').replace('🗣️','').replace('⚙️','').replace('📊','').strip() in k)
                    role_data = pdf_safe_roles[pdf_role_name]
                    
                    resume_text = extract_text(resume_file)
                    if not resume_text:
                        st.error("❌ Cannot read resume. Try another format.")
                    else:
                        st.success("✅ Analysis completed successfully")
                        
                        ml_score = ml_resume_classifier(resume_text)
                        skill_similarity = advanced_ml_similarity(resume_text, role_data['skills']) if not fast_mode else 0.0
                        ats_score_val = advanced_ats_score(resume_text)
                        role_fit_score = int((skill_similarity * 0.5 + ml_score * 0.3 + ats_score_val * 0.2))
                        exp_years = extract_experience_years(resume_text)
                        
                        # NEW CODE: Handle Empty text for roles
                        top_roles = find_best_roles(resume_text)
                        
                        predicted_role, model_confidence, top3_preds = predict_role_from_model(resume_text)
                        
                        st.session_state.results = {
                            'ml_score': ml_score, 
                            'skill_similarity': skill_similarity, 
                            'ats_score': ats_score_val,
                            'role_fit': role_fit_score, 
                            'experience': exp_years,
                            'role': selected_role,
                            'top_roles': top_roles, 
                            'role_data': role_data,
                            'resume_preview': resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,
                            'full_resume': resume_text,
                            'success': True,
                            'predicted_role': predicted_role,
                            'model_confidence': model_confidence,
                            'top3_preds': top3_preds,
                            'mode': 'Single'
                        }
                        # ✨ Streamlit Best Practice: DO NOT call st.rerun() here. 
                        # Letting the script continue naturally guarantees immediate UI update.
                
                else:
                    # NEW CODE: Multiple Resumes Processing
                    multi_results = []
                    my_bar = st.progress(0, text="Initializing processing...")
                    
                    for i, f in enumerate(resume_files):
                        my_bar.progress((i) / len(resume_files), text=f"Processing Resume {i+1}/{len(resume_files)}: {f.name}...")
                        
                        text = extract_text(f)
                        if not text:
                            continue
                        
                        top_roles = find_best_roles(text)
                        auto_role_name = top_roles[0][0] if top_roles else "Software Engineer"
                        auto_role_data = pdf_safe_roles.get(auto_role_name, pdf_safe_roles["Software Engineer"])
                        
                        ml_val = ml_resume_classifier(text)
                        sim_val = advanced_ml_similarity(text, auto_role_data['skills']) if not fast_mode else 0.0
                        ats_val = advanced_ats_score(text)
                        exp_val = extract_experience_years(text)
                        
                        old_role_fit_score = (sim_val * 0.5 + ml_val * 0.3 + ats_val * 0.2)
                        
                        # Apply new user ranking formula
                        final_score = (old_role_fit_score * 0.4) + (sim_val * 0.3) + (ats_val * 0.2) + (ml_val * 0.1)
                        
                        multi_results.append({
                            'name': f.name,
                            'ml_score': ml_val,
                            'skill_similarity': sim_val,
                            'ats_score': ats_val,
                            'role_fit': old_role_fit_score,
                            'final_score': final_score,
                            'experience': exp_val,
                            'full_resume': text,
                            'role_data': auto_role_data,
                            'predicted_role': auto_role_name,
                            'top_roles': top_roles
                        })
                    
                    
                    my_bar.progress(1.0, text="Finalizing results...")
                    
                    if not multi_results:
                        st.error("❌ Could not extract text from any uploaded files.")
                    else:
                        st.success("✅ Analysis completed successfully")
                        multi_results.sort(key=lambda x: x['final_score'], reverse=True)
                        
                        for i, res in enumerate(multi_results):
                            res['rank'] = i + 1
                            
                        st.session_state.multi_results = multi_results
                        st.session_state.results = {'mode': 'Multiple', 'success': True}
                        # ✨ Streamlit Best Practice: DO NOT call st.rerun() here.

# ✅ NEW ORDER: Resume Review FIRST, then Skill Gap, then ML Dashboard
if 'results' in st.session_state and st.session_state.results.get('mode', 'Single') == 'Single' and st.session_state.results.get('success'):
    results = st.session_state.results
    role_data = results['role_data']
    
    # 1. NEW: Comprehensive Resume Review (TOP)
    resume_review_data = comprehensive_resume_review(results['full_resume'])
    display_resume_review(resume_review_data)
    
    # 2. FIXED Skill Gap Analysis
    display_skill_gap_analysis(results)
    
    # 3. ML Analysis Dashboard (existing)
    st.markdown("## 🎯 **🤖 ML Analysis Dashboard**")
    
    metrics = [
        ("Overall Fit", "Role Match", f"{results['role_fit']}%", get_role_fit_reason(results['role_fit'])),
        ("ML Proficiency", "ML Score", f"{int(results['ml_score'])}/100", get_ml_score_reason(results['ml_score'])),
        ("Semantic Match", "TF-IDF Similarity", f"{int(results['skill_similarity'])}%", get_similarity_reason(results['skill_similarity'])),
        ("ATS Score", "ATS Score", f"{int(results['ats_score'])}/100", get_ats_reason(results['ats_score'])),
        ("Experience ✅", "Extracted Years", f"{results['experience']} yrs", get_experience_reason(results['experience'], role_data['exp']))
    ]
    
    for title, label, value, reason in metrics:
        reason_class = "excellent" if "Excellent" in reason else "good" if "Strong" in reason else "average" if "Good" in reason else "needs-work"
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-title">{title}</div>
                <div style="font-size: 2.5rem; font-weight: bold; color: white;">{value}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{label}</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="reason-card {reason_class}">{reason}</div>', unsafe_allow_html=True)

    if results.get('predicted_role'):
        st.markdown("## 🧠 **True Machine Learning Prediction**")
        st.info("Based on your trained ML classification model.")
        colA, colB = st.columns([1, 2])
        with colA:
            st.markdown(f'''
            <div class="metric-card" style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);">
                <div class="metric-title">Predicted Job Role</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: white;">{results['predicted_role']}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">Confidence: {results['model_confidence']:.1f}%</div>
            </div>
            ''', unsafe_allow_html=True)
        with colB:
            st.markdown("#### Top 3 Probabilities")
            for role_name, prob in results['top3_preds']:
                st.progress(float(prob), text=f"{role_name} ({prob*100:.1f}%)")

    st.markdown("## 📊 **ML Analytics Dashboard**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### **📈 Performance Overview**")
        radar_fig = create_radar_chart(
            results['role_fit'], 
            results['ats_score'], 
            results['skill_similarity'], 
            results['ml_score']
        )
        st.pyplot(radar_fig, use_container_width=True)

    with col2:
        st.markdown("### **🏆 Top 5 Role Recommendations**")  # 🔥 FIXED TITLE
        _, pdf_safe_roles = get_all_job_roles()
        
        # 🔥 FIXED: Ensure UNIQUE roles only, NO DUPLICATES!
        unique_top_roles = []
        seen_roles = set()
        for role_name, score in results['top_roles']:
            if role_name not in seen_roles:
                unique_top_roles.append((role_name, score))
                seen_roles.add(role_name)
            if len(unique_top_roles) == 5:
                break
        
        for i, (role_name, score) in enumerate(unique_top_roles):
            reason = get_top_role_reason(role_name, score, results['full_resume'], pdf_safe_roles)
            display_role = remove_emojis(role_name)
            
            st.markdown(f'''
            <div class="role-leaderboard-card">
                <span style="font-size: 2.2rem; font-weight: 800; color: #10b981; margin-right: 1rem;">#{i+1}</span>
                <div style="flex: 1;">
                    <div class="role-name">{display_role}</div>
                    <div class="role-reason">{reason}</div>
                </div>
                <div class="role-score" style="font-size: 2rem; color: #10b981;">{int(score)}%</div>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("### 📊 Score Breakdown")

    col1, col2 = st.columns([2, 1])

    with col1:
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6))

        sizes = [
            results['role_fit'],
            results['skill_similarity'],
            results['ml_score'],
            results['ats_score']
        ]

        labels = [
            f"Role Fit ({results['role_fit']}%)",
            f"Skills ({int(results['skill_similarity'])}%)",
            f"ML Score ({int(results['ml_score'])}%)",
            f"ATS Score ({int(results['ats_score'])}%)"
        ]

        colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']

        wedges, texts = ax_pie.pie(
            sizes,
            labels=labels,
            startangle=90,
            colors=colors,
            wedgeprops={'linewidth': 2, 'edgecolor': 'white'},
            textprops={'fontsize': 12}
        )

        ax_pie.set_title("Score Distribution", fontsize=16, fontweight="bold")
        ax_pie.axis("equal")

        st.pyplot(fig_pie)


    with col2:
        st.markdown("#### 📌 Components")

        st.markdown(f"""
        <div style="font-size:18px; line-height:2;">
        🟢 <b>Role Fit:</b> {results['role_fit']}%<br>
        🔵 <b>Skills:</b> {int(results['skill_similarity'])}%<br>
        🟠 <b>ML Score:</b> {int(results['ml_score'])}%<br>
        🔴 <b>ATS Score:</b> {int(results['ats_score'])}%
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    decision = "🟢 **EXCELLENT - HIRE**" if results['role_fit'] > 85 else "🟡 **STRONG - INTERVIEW**" if results['role_fit'] > 70 else "🔵 **GOOD - DEVELOP**"
    hire_prob = min(95, results['role_fit'] + results['ml_score']*0.5)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 2rem;
            border-radius: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 10px 30px rgba(16,185,129,0.3);
        ">
            <h2 style="margin: 0 0 1rem 0; font-size: 1.8rem;">🤖 **HIRING DECISION**</h2>
            <h1 style="margin: 0; font-size: 3rem; font-weight: bold;">{decision}</h1>
            <p style="margin: 1rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                Hire Probability: <strong>{int(hire_prob)}%</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        pdf_data = create_pdf_report(results, role_data)
        st.download_button(
            label="📥 **Download ML Report as PDF**", 
            data=pdf_data,
            file_name=f"AI_Talent_Scout_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        report = f"""AI TALENT SCOUT PRO - ML ANALYSIS REPORT
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Role Analyzed: {remove_emojis(results['role'])}

ML SCORES:
Overall Fit: {results['role_fit']}%
ML Proficiency: {int(results['ml_score'])}/100
TF-IDF Similarity: {int(results['skill_similarity'])}%
ATS Score: {int(results['ats_score'])}/100
Experience: {results['experience']} years

RECOMMENDATION: {decision}
BEST MATCH: {remove_emojis(results['top_roles'][0][0])} ({int(results['top_roles'][0][1])}%)
POWERED BY: TF-IDF + Machine Learning Models"""
        st.download_button(
            label="📄 **Download as TXT**", 
            data=report,
            file_name=f"ml_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    if st.button("🔄 **New Analysis**", type="secondary", use_container_width=True):
        if 'results' in st.session_state:
            del st.session_state.results
        if 'multi_results' in st.session_state:
            del st.session_state.multi_results
        st.rerun()

# NEW CODE: Multiple Resume Mode UI display
if 'results' in st.session_state and st.session_state.results.get('mode') == 'Multiple' and 'multi_results' in st.session_state:
    multi_results = st.session_state.multi_results
    
    st.markdown("## 📊 **Multiple Resume Comparison**")
    
    df_data = []
    for res in multi_results:
        df_data.append({
            "Rank": res['rank'],
            "Name": res['name'],
            "Role Fit": f"{res['role_fit']:.1f}",
            "ATS": f"{res['ats_score']:.1f}",
            "ML Score": f"{res['ml_score']:.1f}",
            "Skills": f"{res['skill_similarity']:.1f}",
            "Experience": f"{res['experience']} yrs",
            "Final Score": f"{res['final_score']:.1f}"
        })
    df = pd.DataFrame(df_data)
    st.table(df)
    
    st.markdown("### 📈 **Role Fit / Final Score Comparison**")
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [r['name'] for r in multi_results]
    scores = [r['final_score'] for r in multi_results]
    sns.barplot(x=scores, y=names, palette="viridis", ax=ax)
    ax.set_xlabel("Final Score")
    ax.set_title("Candidate Rankings")
    st.pyplot(fig)
    
    st.markdown("### 🔍 **Candidate Details**")
    for res in multi_results:
        with st.expander(f"#{res['rank']} - {res['name']} (Final Score: {res['final_score']:.1f} | Role: {res['predicted_role']})"):
            res_dummy = {
                'ml_score': res['ml_score'],
                'skill_similarity': res['skill_similarity'],
                'ats_score': res['ats_score'],
                'role_fit': int(res['role_fit']), 
                'experience': res['experience'],
                'role_data': res['role_data'],
                'full_resume': res['full_resume'],
                'success': True
            }
            
            # 1. 📊 Hire Probability (NEW)
            hire_prob = min(95, res['role_fit'] + res['ml_score'] * 0.5)
            decision = "EXCELLENT - HIRE" if hire_prob > 85 else "STRONG - INTERVIEW" if hire_prob > 70 else "GOOD - DEVELOP"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1.5rem; border-radius: 15px; text-align: center; color: white; margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; font-size: 1.2rem; opacity: 0.9;">🤖 **HIRING DECISION**</h3>
                <h2 style="margin: 0.5rem 0; font-size: 2.2rem; font-weight: bold;">{decision}</h2>
                <div style="font-size: 1.1rem; opacity: 0.9;">
                    Hire Probability: <strong>{int(hire_prob)}%</strong> <br>
                    Target Role Predict: <strong>{res['predicted_role']}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. 📋 Resume Review
            rev_data = comprehensive_resume_review(res['full_resume'])
            display_resume_review(rev_data)
            
            # 3. 🎯 Skill Coverage Analysis (MODIFIED SECTION)
            display_skill_coverage(res_dummy)
            
            # 4. 🤖 ML Metrics
            st.markdown("#### **🤖 Metrics Overview**")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Role Fit", f"{int(res['role_fit'])}%")
            col2.metric("ATS Score", f"{int(res['ats_score'])}")
            col3.metric("ML Score", f"{int(res['ml_score'])}")
            col4.metric("Skill Sim", f"{int(res['skill_similarity'])}%")
            col5.metric("Experience", f"{res['experience']} yrs")
            
            # 5. 🧠 Reasoning (NEW)
            st.markdown("#### **🧠 AI Reasoning**")
            st.info(f"**Role Fit:** {get_role_fit_reason(res['role_fit'])}")
            st.info(f"**ATS Breakdown:** {get_ats_reason(res['ats_score'])}")
            st.info(f"**Skills Overlap:** {get_similarity_reason(res['skill_similarity'])}")
            
            # 6. 📈 Improvements Needed (NEW)
            st.markdown("#### **📈 Improvements Needed**")
            improvements = []
            
            if rev_data["action_verbs"] < 3:
                improvements.append("Use more strong action verbs (e.g., developed, implemented, designed).")
            if not rev_data["has_quant"]:
                improvements.append("Add quantifiable results to your achievements (e.g., increased revenue by 20%, saved 10 hours).")
            if res['ats_score'] < 60:
                improvements.append("Improve ATS formatting. Ensure standard sections (Experience, Education, Skills) are clearly distinct.")

            if not improvements:
                st.success("Resume is exceptionally optimized! Keep up the good work.")
            else:
                for imp in improvements:
                    st.markdown(f"- {imp}")
            
            # 7. 🏆 Top Role Suggestions
            st.markdown("#### **🏆 Top Role Alternatives**")
            for i, (r_name, r_score) in enumerate(res['top_roles'][:3]):
                st.markdown(f"**{i+1}.** {r_name} ({int(r_score)}% match)")
            
            st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 **New Analysis**", type="secondary", use_container_width=True, key="multi_reset"):
        if 'results' in st.session_state:
            del st.session_state.results
        if 'multi_results' in st.session_state:
            del st.session_state.multi_results
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align:center;color:#64748b;'>🤖 AI Talent Scout Pro © 2026 | Powered by TF-IDF + ML Models | 50+ Roles</p>", unsafe_allow_html=True)
