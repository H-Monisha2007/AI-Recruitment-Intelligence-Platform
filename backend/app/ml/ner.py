import spacy
from spacy.matcher import PhraseMatcher
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class NERService:
    def __init__(self):
        try:
            self.nlp = spacy.load(settings.SPACY_MODEL)
            logger.info(f"Loaded spaCy model: {settings.SPACY_MODEL}")
        except Exception:
            logger.warning(f"spaCy model {settings.SPACY_MODEL} not found. Attempting to download...")
            spacy.cli.download(settings.SPACY_MODEL)
            self.nlp = spacy.load(settings.SPACY_MODEL)
            
        self.matcher = PhraseMatcher(self.nlp.vocab)
        # We can add custom phrases here later for better skill detection

    def extract_skills(self, text: str) -> list[str]:
        doc = self.nlp(text)
        skills = []
        
        # Basic NER for ORG/PRODUCT which often contain tech names
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART"]:
                skills.append(ent.text)
        
        # Deduplicate and clean
        return list(set([s.strip() for s in skills if len(s) > 1]))

    def extract_entities(self, text: str) -> dict:
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
        return entities
