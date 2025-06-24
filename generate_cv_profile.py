#!/usr/bin/env python3
"""
GitHub Profile CV Generator
Generates a markdown CV from GitHub profile data and resume information
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse
import pytesseract
from PIL import Image
import requests
from pathlib import Path

class CVGenerator:
    def __init__(self, ollama_model: str = "llama2"):
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from {image_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
            return text.strip()
        except ImportError:
            print("PyMuPDF not installed. Install with: pip install PyMuPDF")
            return ""
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""
    
    def parse_resume_with_llm(self, resume_text: str) -> Dict[str, Any]:
        """Parse resume text using LLM"""
        prompt = f"""
        Extract structured information from this resume text and return it as JSON with the following fields:
        - name: full name
        - email: email address
        - phone: phone number
        - location: location/address
        - summary: professional summary
        - skills: list of technical skills
        - education: list of education entries with degree, institution, year
        - experience: list of work experience with title, company, duration, description
        - certifications: list of certifications
        
        Resume text:
        {resume_text}
        
        Return only valid JSON:
        """
        
        response = self.call_ollama(prompt)
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}
        except:
            return {}
    
    def analyze_github_projects(self, github_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze and categorize GitHub projects"""
        projects = []
        
        # Sort projects by featured level and stars
        sorted_repos = sorted(
            github_data.items(),
            key=lambda x: (x[1].get('featuredLevel', 0), x[1].get('stars', 0)),
            reverse=True
        )
        
        for repo_name, repo_data in sorted_repos:
            project = {
                'name': repo_name,
                'description': repo_data.get('description', ''),
                'stars': repo_data.get('stars', 0),
                'featured_level': repo_data.get('featuredLevel', 0),
                'languages': self._get_primary_languages(repo_data.get('language_distribution', {})),
                'lines_of_code': repo_data.get('actual_code_lines', 0),
                'commits': repo_data.get('contributions', {}).get('total_commits', 0),
                'is_private': repo_data.get('private', False)
            }
            projects.append(project)
        
        return projects
    
    def _get_primary_languages(self, lang_dist: Dict[str, int]) -> List[str]:
        """Get primary programming languages from distribution"""
        # Map file extensions to language names
        ext_to_lang = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.html': 'HTML',
            '.css': 'CSS',
            '.svelte': 'Svelte',
            '.vue': 'Vue.js',
            '.jsx': 'React',
            '.tsx': 'React/TypeScript'
        }
        
        languages = []
        for ext, lines in sorted(lang_dist.items(), key=lambda x: x[1], reverse=True):
            if ext in ext_to_lang and lines > 10:  # Only include significant usage
                languages.append(ext_to_lang[ext])
        
        return languages[:3]  # Return top 3 languages
    
    def generate_skills_from_projects(self, projects: List[Dict[str, Any]]) -> List[str]:
        """Generate skills list from GitHub projects"""
        skills = set()
        
        for project in projects:
            skills.update(project['languages'])
        
        # Add common related skills
        skill_mapping = {
            'Python': ['Django', 'Flask', 'FastAPI', 'NumPy', 'Pandas'],
            'JavaScript': ['Node.js', 'Express.js', 'React', 'Vue.js'],
            'TypeScript': ['Angular', 'React', 'Node.js'],
            'HTML': ['CSS', 'Bootstrap', 'Responsive Design'],
            'CSS': ['Sass', 'Bootstrap', 'Tailwind CSS']
        }
        
        for lang in list(skills):
            if lang in skill_mapping:
                skills.update(skill_mapping[lang][:2])  # Add top 2 related skills
        
        return sorted(list(skills))
    
    def generate_cv_markdown(self, resume_data: Dict[str, Any], github_data: Dict[str, Any], 
                           personal_info: Optional[Dict[str, Any]] = None) -> str:
        """Generate the final CV markdown"""
        
        projects = self.analyze_github_projects(github_data)
        github_skills = self.generate_skills_from_projects(projects)
        
        # Merge skills from resume and GitHub
        all_skills = set(resume_data.get('skills', []) + github_skills)
        
        # Calculate GitHub stats
        total_repos = len([p for p in projects if not p['is_private']])
        total_stars = sum(p['stars'] for p in projects)
        total_commits = sum(p['commits'] for p in projects)
        total_loc = sum(p['lines_of_code'] for p in projects)
        
        # Generate markdown
        cv_content = f"""# {resume_data.get('name', 'Your Name')}

## Contact Information
- **Email:** {resume_data.get('email', 'your.email@example.com')}
- **Phone:** {resume_data.get('phone', 'Your Phone')}
- **Location:** {resume_data.get('location', 'Your Location')}

## Professional Summary
{resume_data.get('summary', 'Professional software developer with expertise in multiple programming languages and technologies.')}

## GitHub Statistics
- **Public Repositories:** {total_repos}
- **Total Stars:** {total_stars}
- **Total Commits:** {total_commits:,}
- **Lines of Code:** {total_loc:,}

## Technical Skills
{self._format_skills_list(sorted(all_skills))}

## Featured Projects
{self._format_projects(projects[:5])}  # Top 5 projects

## Professional Experience
{self._format_experience(resume_data.get('experience', []))}

## Education
{self._format_education(resume_data.get('education', []))}

## Certifications
{self._format_certifications(resume_data.get('certifications', []))}

---
"""
        return cv_content
    
    def _format_skills_list(self, skills: List[str]) -> str:
        """Format skills as markdown list"""
        if not skills:
            return "- No skills data available"
        
        # Group skills by category (simple heuristic)
        categories = {
            'Languages': [],
            'Frameworks': [],
            'Tools': [],
            'Other': []
        }
        
        frameworks = {'Django', 'Flask', 'FastAPI', 'React', 'Vue.js', 'Angular', 'Express.js', 'Svelte'}
        languages = {'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C', 'C#', 'PHP', 'Ruby', 'Go', 'Rust'}
        tools = {'Git', 'Docker', 'AWS', 'Linux', 'SQL', 'MongoDB', 'PostgreSQL'}
        
        for skill in skills:
            if skill in languages:
                categories['Languages'].append(skill)
            elif skill in frameworks:
                categories['Frameworks'].append(skill)
            elif skill in tools:
                categories['Tools'].append(skill)
            else:
                categories['Other'].append(skill)
        
        result = []
        for category, items in categories.items():
            if items:
                result.append(f"- **{category}:** {', '.join(items)}")
        
        return '\n'.join(result)
    
    def _format_projects(self, projects: List[Dict[str, Any]]) -> str:
        """Format projects as markdown"""
        if not projects:
            return "No projects available."
        
        result = []
        for project in projects:
            stars_text = f" ⭐ {project['stars']}" if project['stars'] > 0 else ""
            languages = ", ".join(project['languages']) if project['languages'] else "Mixed"
            
            result.append(f"""### {project['name']}{stars_text}
**Languages:** {languages}  
**Lines of Code:** {project['lines_of_code']:,}  
**Commits:** {project['commits']}

{project['description']}
""")
        
        return '\n'.join(result)
    
    def _format_experience(self, experience: List[Dict[str, Any]]) -> str:
        """Format work experience as markdown"""
        if not experience:
            return "No work experience data available."
        
        result = []
        for exp in experience:
            result.append(f"""### {exp.get('title', 'Position')} - {exp.get('company', 'Company')}
**Duration:** {exp.get('duration', 'Duration')}

{exp.get('description', 'Job description not available.')}
""")
        
        return '\n'.join(result)
    
    def _format_education(self, education: List[Dict[str, Any]]) -> str:
        """Format education as markdown"""
        if not education:
            return "No education data available."
        
        result = []
        for edu in education:
            result.append(f"- **{edu.get('degree', 'Degree')}** - {edu.get('institution', 'Institution')} ({edu.get('year', 'Year')})")
        
        return '\n'.join(result)
    
    def _format_certifications(self, certifications: List[str]) -> str:
        """Format certifications as markdown"""
        if not certifications:
            return "No certifications data available."
        
        return '\n'.join([f"- {cert}" for cert in certifications])

def main():
    parser = argparse.ArgumentParser(description='Generate CV from GitHub data and resume')
    parser.add_argument('--github-data', required=True, help='Path to GitHub data JSON file')
    parser.add_argument('--resume', required=True, help='Path to resume file (PDF or image)')
    parser.add_argument('--output', default='cv.md', help='Output markdown file path')
    parser.add_argument('--ollama-model', default='llama2', help='Ollama model to use')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = CVGenerator(args.ollama_model)
    
    # Load GitHub data
    try:
        with open(args.github_data, 'r', encoding='utf-8') as f:
            github_data = json.load(f)
        print(f"Loaded GitHub data with {len(github_data)} repositories")
    except Exception as e:
        print(f"Error loading GitHub data: {e}")
        sys.exit(1)
    
    # Extract resume text
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Resume file not found: {args.resume}")
        sys.exit(1)
    
    print("Extracting text from resume...")
    if resume_path.suffix.lower() == '.pdf':
        resume_text = generator.extract_text_from_pdf(args.resume)
    else:
        resume_text = generator.extract_text_from_image(args.resume)
    
    if not resume_text:
        print("Failed to extract text from resume")
        sys.exit(1)
    
    print("Parsing resume with LLM...")
    resume_data = generator.parse_resume_with_llm(resume_text)
    
    if not resume_data:
        print("Failed to parse resume data")
        # Use basic fallback
        resume_data = {
            'name': 'Your Name',
            'email': 'your.email@example.com',
            'phone': 'Your Phone',
            'location': 'Your Location',
            'summary': 'Software developer with GitHub projects',
            'skills': [],
            'experience': [],
            'education': [],
            'certifications': []
        }
    
    print("Generating CV...")
    cv_content = generator.generate_cv_markdown(resume_data, github_data)
    
    # Save CV
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(cv_content)
    
    print(f"CV generated successfully: {args.output}")

if __name__ == "__main__":
    main()