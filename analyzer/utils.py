import re 


COMMON_SKILLS = [
    "python", "java", "c++", "django", "flask", "react", "javascript", "html","css", "node", "sql", "mysql", "mongodb", "aws", "docker", "git", "machine learning", "ui/ux", "ux/ui", "ui", "ux", "figma", "photoshop", "illustrator", "excel", "framer", "selenium", "c", "teamwork", "communication", "problem solving", "time management", "sales", "marketing", "research", "creativity", 
] 


def extract_keywords(text):
    text_lower = text.lower()
    found_skills = [skill for skill in COMMON_SKILLS if re.search(rf'\b{skill}\b', text_lower)]

    return list(set(found_skills)) #no duplicates 