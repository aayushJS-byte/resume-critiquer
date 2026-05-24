from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ANALYZE_PROMPT = """
You are an elite ATS (Applicant Tracking System) resume analyzer, career coach, and hiring expert with 20+ years experience.
Respond ONLY in valid JSON. No extra text, no markdown, just raw JSON.

{
  "ats_score": <integer 0-100>,
  "score_breakdown": {
    "keywords": <0-25>,
    "formatting": <0-25>,
    "experience_clarity": <0-25>,
    "contact_and_structure": <0-25>
  },
  "grade": <"A+"|"A"|"B+"|"B"|"C+"|"C"|"D"|"F">,
  "strengths": ["detailed strength 1", "detailed strength 2", "detailed strength 3"],
  "improvements": [
    {"issue": "specific issue", "suggestion": "actionable fix", "priority": "high|medium|low"},
    {"issue": "...", "suggestion": "...", "priority": "..."}
  ],
  "missing_keywords": ["keyword1", "keyword2", "keyword3"],
  "skills_found": ["skill1", "skill2", "skill3"],
  "experience_years": <estimated integer or null>,
  "seniority_level": <"Intern"|"Junior"|"Mid"|"Senior"|"Lead"|"Executive">,
  "top_roles": ["Best Fit Role 1", "Best Fit Role 2", "Best Fit Role 3"],
  "industry_fit": ["Industry 1", "Industry 2"],
  "summary": "3-4 sentence overall assessment with specific observations",
  "rewritten_summary": "A professionally rewritten resume summary/objective for this candidate (3-4 sentences)",
  "quick_wins": ["Fast actionable tip 1", "Fast actionable tip 2", "Fast actionable tip 3"],
  "red_flags": ["any red flag or empty array"],
  "certifications_recommended": ["Cert 1", "Cert 2"],
  "salary_range": {"min": <integer USD>, "max": <integer USD>, "currency": "USD"}
}
"""

COVER_LETTER_PROMPT = """
You are an expert career coach. Write a compelling, personalized cover letter based on the resume and job description provided.
The cover letter should be professional, specific, and 3-4 paragraphs. Start directly with "Dear Hiring Manager," — no preamble.
"""

INTERVIEW_PROMPT = """
You are a senior hiring manager. Based on this resume and job description, generate likely interview questions.
Respond ONLY in valid JSON:
{
  "behavioral": ["question1", "question2", "question3", "question4", "question5"],
  "technical": ["question1", "question2", "question3", "question4", "question5"],
  "situational": ["question1", "question2", "question3"],
  "questions_to_ask": ["Smart question candidate should ask 1", "Smart question candidate should ask 2", "Smart question candidate should ask 3"]
}
"""

REWRITE_BULLET_PROMPT = """
You are a professional resume writer. Rewrite the following resume bullet points to be stronger, more impactful, and ATS-friendly.
Use strong action verbs, quantify where possible, and follow the STAR method.
Respond ONLY in valid JSON:
{
  "rewritten_bullets": ["• Rewritten bullet 1", "• Rewritten bullet 2", "• Rewritten bullet 3"]
}
"""

COMPARE_PROMPT = """
You are an expert resume consultant. Compare these two resumes and provide analysis.
Respond ONLY in valid JSON:
{
  "winner": "Resume A" | "Resume B" | "Tie",
  "resume_a_score": <0-100>,
  "resume_b_score": <0-100>,
  "resume_a_strengths": ["strength1", "strength2"],
  "resume_b_strengths": ["strength1", "strength2"],
  "resume_a_weaknesses": ["weakness1", "weakness2"],
  "resume_b_weaknesses": ["weakness1", "weakness2"],
  "recommendation": "Which to use and why in 2-3 sentences"
}
"""


def call_groq(system: str, user: str, temperature: float = 0.3, json_mode: bool = True) -> str:
    kwargs = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": temperature,
        "max_tokens": 2048,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def analyze_resume(resume_text: str, job_description: str = "") -> dict:
    user_content = f"RESUME:\n{resume_text}"
    if job_description.strip():
        user_content += f"\n\nJOB DESCRIPTION:\n{job_description}"
    raw = call_groq(ANALYZE_PROMPT, user_content)
    return json.loads(raw)


def generate_cover_letter(resume_text: str, job_description: str, tone: str = "Professional") -> str:
    user_content = f"TONE: {tone}\n\nRESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{job_description}"
    return call_groq(COVER_LETTER_PROMPT, user_content, temperature=0.7, json_mode=False)


def generate_interview_questions(resume_text: str, job_description: str = "") -> dict:
    user_content = f"RESUME:\n{resume_text}"
    if job_description.strip():
        user_content += f"\n\nJOB DESCRIPTION:\n{job_description}"
    raw = call_groq(INTERVIEW_PROMPT, user_content)
    return json.loads(raw)


def rewrite_bullets(bullets_text: str) -> dict:
    raw = call_groq(REWRITE_BULLET_PROMPT, f"BULLETS TO REWRITE:\n{bullets_text}")
    return json.loads(raw)


def compare_resumes(resume_a: str, resume_b: str) -> dict:
    user_content = f"RESUME A:\n{resume_a}\n\n---\n\nRESUME B:\n{resume_b}"
    raw = call_groq(COMPARE_PROMPT, user_content)
    return json.loads(raw)