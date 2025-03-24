import re
import importlib
import sys
import subprocess
import importlib
from typing import Dict, List, Any
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
#import spacy
def install_and_import(package):
    try:
        importlib.import_module(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    finally:
        globals()[package] = importlib.import_module(package)

install_and_import('spacy')
install_and_import('nltk')
install_and_import('PyPDF2')
install_and_import('streamlit')
from pdfminer.high_level import extract_text
import PyPDF2
import io
#import streamlit as st
from pdfminer.high_level import extract_text

# Automatically download ALL required NLTK resources
print("Ensuring all NLTK resources are available...")
nltk.download('punkt')

# Modify the sent_tokenize function to avoid the punkt_tab issue
def safe_sent_tokenize(text):
    """
    A safer version of sent_tokenize that doesn't rely on punkt_tab
    """
    # Simple sentence tokenization based on common sentence delimiters
    sentences = []
    current_sentence = ""
    
    # Split by common sentence endings
    for char in text:
        current_sentence += char
        if char in ['.', '!', '?'] and len(current_sentence.strip()) > 0:
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    # Add any remaining text as a sentence
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    return sentences

# Make sure to install dependencies:
# pip install nltk spacy PyPDF2 streamlit pdfminer.six
# python -m spacy download en_core_web_sm

class SyllabusTagger:
    def __init__(self):
        # Load NLP models
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading missing spaCy model: en_core_web_sm...")
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            spacy.load("en_core_web_sm")  # Load after installation
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Please install spaCy models with: python -m spacy download en_core_web_sm")
            raise
            
        # Keywords and phrases for each tag category - updated attendance keywords
        self.keywords = {
            "project_heavy": [
                "project", "projects", "group project", "individual project", "final project",
                "team project", "research project", "design project", "project-based",
                "deliverable", "portfolio", "case study"
            ],
            "exam_heavy": [
                "exam", "exams", "midterm", "midterms", "final exam", "quiz", "quizzes", 
                "test", "tests", "assessment", "assessments", "examination"
            ],
            "assignment_heavy": [
                "assignment", "assignments", "homework", "homeworks", "problem set", 
                "problem sets", "exercise", "exercises", "lab", "labs", "paper", "papers",
                "essay", "essays", "report", "reports", "writing", "readings"
            ],
            "needs_prerequisite": [
                "prerequisite", "prerequisites", "prior knowledge", "required course",
                "required courses", "previous course", "previous courses", "co-requisite",
                "foundations", "background in", "familiarity with", "experience with"
            ],
            "attendance_required": [
                "attendance", "attendances", "mandatory", "required", "participate", 
                "participation", "present", "presence", "absence", "absences", 
                "miss class", "missing class", "attend", "expected to attend", 
                "students are expected", "arrive on time", "classroom participation",
                "attendance policy", "attend class", "attendance grade"
            ]
        }
        
        # Threshold values for each tag
        self.thresholds = {
            "project_heavy": {
                "keyword_threshold": 5,  # Number of project-related keywords
                "grade_threshold": 25    # Project percentage of final grade
            },
            "exam_heavy": {
                "keyword_threshold": 7,  # Number of exam-related keywords
                "grade_threshold": 30    # Exam percentage of final grade
            },
            "assignment_heavy": {
                "keyword_threshold": 10, # Number of assignment-related keywords
                "grade_threshold": 40    # Assignment percentage of final grade
            },
            "needs_prerequisite": {
                "keyword_threshold": 2   # Number of prerequisite-related phrases
            },
            "attendance_required": {
                "keyword_threshold": 3,  # Number of attendance-related keywords
                "policy_strength": 0.3   # Reduced threshold to be more sensitive
            }
        }
    
    def extract_grade_distribution(self, text: str) -> Dict[str, float]:
        """
        Extracts the grade distribution from syllabus text.
        Enhanced to recognize more grade formats common in syllabi.
        """
        grade_dict = {}
        
        # Look for more flexible grade patterns
        grade_patterns = [
            # Standard percentage pattern
            r"(?i)(project|projects|final project|team project).*?(\d+)%",
            r"(?i)(exam|exams|midterm|final exam).*?(\d+)%",
            r"(?i)(assignment|assignments|homework).*?(\d+)%",
            r"(?i)(quiz|quizzes).*?(\d+)%",
            r"(?i)(participation|attendance).*?(\d+)%",
            
            # Points-based patterns
            r"(?i)(project|projects|final project|team project).*?(\d+)\s*(pts|points)",
            r"(?i)(exam|exams|midterm|final exam).*?(\d+)\s*(pts|points)",
            r"(?i)(assignment|assignments|homework).*?(\d+)\s*(pts|points)",
            r"(?i)(quiz|quizzes).*?(\d+)\s*(pts|points)",
            r"(?i)(participation|attendance).*?(\d+)\s*(pts|points)",
            
            # Table format (common in syllabi like yours)
            r"(?i)(project|projects|final project|team project)\s*(\d+)",
            r"(?i)(exam|exams|midterm|final exam)\s*(\d+)",
            r"(?i)(assignment|assignments|homework)\s*(\d+)",
            r"(?i)(quiz|quizzes)\s*(\d+)",
            r"(?i)(participation|attendance)\s*(\d+)"
        ]
        
        # Look for total points in the grading section to calculate percentages if needed
        total_points_match = re.search(r"(?i)total.*?(\d+)", text)
        total_points = 100  # Default to 100 if not specified
        if total_points_match:
            try:
                total_points = float(total_points_match.group(1))
            except ValueError:
                pass
        
        # Search for grade components
        for pattern in grade_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                component = match[0].lower()
                try:
                    # Try to convert the value to float
                    percentage = float(match[1])
                    
                    # If the grading is points-based, convert to percentage
                    if "pts" in pattern or "points" in pattern or total_points != 100:
                        percentage = (percentage / total_points) * 100
                    
                    # Categorize the component
                    if any(kw in component for kw in self.keywords["project_heavy"]):
                        grade_dict["project"] = grade_dict.get("project", 0) + percentage
                    elif any(kw in component for kw in self.keywords["exam_heavy"]):
                        grade_dict["exam"] = grade_dict.get("exam", 0) + percentage
                    elif any(kw in component for kw in self.keywords["assignment_heavy"]):
                        grade_dict["assignment"] = grade_dict.get("assignment", 0) + percentage
                    elif any(kw in component for kw in self.keywords["attendance_required"]):
                        # Add attendance as a specific category
                        grade_dict["attendance"] = grade_dict.get("attendance", 0) + percentage
                except (ValueError, IndexError):
                    continue
        
        # Special handling for "Team Project" (which is likely project_heavy)
        team_project_match = re.search(r"(?i)team\s*project.*?(\d+)", text)
        if team_project_match:
            try:
                percentage = float(team_project_match.group(1))
                if total_points != 100:
                    percentage = (percentage / total_points) * 100
                grade_dict["project"] = grade_dict.get("project", 0) + percentage
            except ValueError:
                pass
        
        return grade_dict
    
    def analyze_attendance_policy(self, text: str) -> float:
        """
        Analyzes the attendance policy and returns a strength score from 0 to 1.
        Improved to catch more attendance-related phrases and grading elements.
        """
        # Use our safe version of sentence tokenizer to avoid punkt_tab issues
        attendance_sentences = []
        
        # First check for attendance in grade evaluation section
        grade_related = re.search(r"(?i)(grading|evaluation|assessment).*?(attendance|participation|present)", text, re.DOTALL)
        if grade_related:
            # If attendance appears in grading section, this is a strong indicator
            attendance_sentences.append(grade_related.group(0))
            
        # Look for specific sections about attendance
        attendance_section = re.search(r"(?i)(attendance|participation).*?policy[:\n].*?(\n\n|\n\s*\n)", text, re.DOTALL)
        if attendance_section:
            attendance_sentences.append(attendance_section.group(0))
        
        # Get individual sentences containing attendance keywords
        for sentence in safe_sent_tokenize(text):
            if any(kw in sentence.lower() for kw in self.keywords["attendance_required"]):
                attendance_sentences.append(sentence)
        
        if not attendance_sentences:
            return 0.0
        
        # Score the strength of the attendance policy
        strength = 0.0
        
        # Add additional phrases commonly found in syllabi
        strong_phrases = [
            "mandatory", "required", "must attend", "will be taken", 
            "grade will be affected", "participation grade", "expected to attend",
            "students are expected to", "attendance will be", "counted toward", 
            "attendance is part of", "attendance & participation", "attendance and participation"
        ]
        
        moderate_phrases = [
            "expected to attend", "should attend", "attendance is important",
            "regular attendance", "attendance contributes", "attendance affects"
        ]
        
        weak_phrases = [
            "encouraged to attend", "recommended", "attendance helps", 
            "attendance is encouraged", "should try to attend"
        ]
        
        # Check for attendance in grading criteria
        grade_match = re.search(r"(?i)(attendance|participation).*?(\d+)(?:%|\s*points|\s*pts)", text)
        if grade_match:
            # If attendance is explicitly part of the grade, increase strength significantly
            strength += 0.6
        
        for sentence in attendance_sentences:
            sentence_lower = sentence.lower()
            
            # Check for strong enforcement language
            if any(phrase in sentence_lower for phrase in strong_phrases):
                strength += 0.4
            elif any(phrase in sentence_lower for phrase in moderate_phrases):
                strength += 0.2
            elif any(phrase in sentence_lower for phrase in weak_phrases):
                strength += 0.1
            
            # Check for specific absence limits or penalties
            if re.search(r"(?i)(no more than|only|limit of|up to|maximum of)\s*(\d+)\s*(absences|missed)", sentence_lower):
                strength += 0.4
                
            # Check for explicit phrases about attendance affecting grades
            if re.search(r"(?i)(affect|impact|influence|determine).*?(grade|score|evaluation|assessment)", sentence_lower):
                strength += 0.3
        
        # Additional keywords specific to your syllabus format
        extra_points = 0.0
        extra_keywords = ["arrive on time", "expected to attend", "attend class"]
        for keyword in extra_keywords:
            if keyword in text.lower():
                extra_points += 0.15
        
        return min(1.0, strength + extra_points)
    
    
    def check_prerequisites(self, text: str) -> Dict[str, Any]:
        """
        Checks for prerequisites mentioned in the syllabus.
        """
        prereq_count = 0
        prereq_courses = []
        
        # Look for prerequisite section
        prereq_section = re.search(r"(?i)prerequisite[s]?:(.+?)(?:\n\n|\n\s*\n)", text)
        if prereq_section:
            prereq_text = prereq_section.group(1)
            prereq_count += 3  # Weight the dedicated section higher
            
            # Extract course codes
            course_codes = re.findall(r"[A-Z]{2,4}\s*\d{3,4}[A-Z]?", prereq_text)
            prereq_courses.extend(course_codes)
        
        # Count prerequisite keywords
        for keyword in self.keywords["needs_prerequisite"]:
            prereq_count += len(re.findall(r"\b" + re.escape(keyword) + r"\b", text, re.IGNORECASE))
        
        return {
            "count": prereq_count,
            "courses": prereq_courses,
            "has_prerequisites": prereq_count >= self.thresholds["needs_prerequisite"]["keyword_threshold"]
        }
    
    def count_keyword_occurrences(self, text: str, category: str) -> int:
        """
        Counts occurrences of keywords for a specific category.
        """
        count = 0
        text_lower = text.lower()
        
        for keyword in self.keywords[category]:
            # Use word boundary to match whole words
            count += len(re.findall(r"\b" + re.escape(keyword) + r"\b", text_lower))
            
        return count
    
    def generate_tags(self, syllabus_text: str) -> Dict[str, dict]:
        """
        Analyzes syllabus text and generates appropriate tags.
        """
        # Clean up the text
        syllabus_text = syllabus_text.replace('\t', ' ')
        
        # Extract grade distribution
        grade_distribution = self.extract_grade_distribution(syllabus_text)
        
        # Analyze attendance policy
        attendance_strength = self.analyze_attendance_policy(syllabus_text)
        
        # Check prerequisites
        prereq_info = self.check_prerequisites(syllabus_text)
        
        # Count keywords for each category
        project_count = self.count_keyword_occurrences(syllabus_text, "project_heavy")
        exam_count = self.count_keyword_occurrences(syllabus_text, "exam_heavy")
        assignment_count = self.count_keyword_occurrences(syllabus_text, "assignment_heavy")
        
        # Generate tags based on thresholds and analyses
        tags = {
            "project_heavy": {
                "is_tagged": (
                    project_count >= self.thresholds["project_heavy"]["keyword_threshold"] or
                    grade_distribution.get("project", 0) >= self.thresholds["project_heavy"]["grade_threshold"]
                ),
                "keyword_count": project_count,
                "db_id": 2,
            },
            "exam_heavy": {
                "is_tagged": (
                    exam_count >= self.thresholds["exam_heavy"]["keyword_threshold"] or
                    grade_distribution.get("exam", 0) >= self.thresholds["exam_heavy"]["grade_threshold"]
                ),
                "keyword_count": exam_count,
                "db_id": 1,
            },
            "assignment_heavy": {
                "is_tagged": (
                    assignment_count >= self.thresholds["assignment_heavy"]["keyword_threshold"] or
                    grade_distribution.get("assignment", 0) >= self.thresholds["assignment_heavy"]["grade_threshold"]
                ),
                "keyword_count": assignment_count,
                "db_id": 3,
            },
            "needs_prerequisite": {
                "is_tagged": prereq_info["has_prerequisites"],
                "keyword_count": prereq_info["count"],
                "db_id": 4,
            },
            "attendance_required": {
                "is_tagged": attendance_strength >= self.thresholds["attendance_required"]["policy_strength"],
                "attendance_strength": attendance_strength,
                "db_id": 5,
            }
        }
        
        return tags
    
    def get_tag_reasoning(self, syllabus_text: str) -> Dict[str, Dict]:
        """
        Provides detailed reasoning for why each tag was assigned.
        """
        # Clean up the text
        syllabus_text = syllabus_text.replace('\t', ' ')
        
        reasoning = {}
        
        # Extract grade distribution
        grade_distribution = self.extract_grade_distribution(syllabus_text)
        
        # Analyze attendance policy
        attendance_strength = self.analyze_attendance_policy(syllabus_text)
        
        # Check prerequisites
        prereq_info = self.check_prerequisites(syllabus_text)
        
        # Count keywords for each category
        project_count = self.count_keyword_occurrences(syllabus_text, "project_heavy")
        exam_count = self.count_keyword_occurrences(syllabus_text, "exam_heavy")
        assignment_count = self.count_keyword_occurrences(syllabus_text, "assignment_heavy")
        
        # Project heavy reasoning
        reasoning["project_heavy"] = {
            "is_tagged": (
                project_count >= self.thresholds["project_heavy"]["keyword_threshold"] or
                grade_distribution.get("project", 0) >= self.thresholds["project_heavy"]["grade_threshold"]
            ),
            "keyword_count": project_count,
            "keyword_threshold": self.thresholds["project_heavy"]["keyword_threshold"],
            "grade_percentage": grade_distribution.get("project", 0),
            "grade_threshold": self.thresholds["project_heavy"]["grade_threshold"]
        }
        
        # Exam heavy reasoning
        reasoning["exam_heavy"] = {
            "is_tagged": (
                exam_count >= self.thresholds["exam_heavy"]["keyword_threshold"] or
                grade_distribution.get("exam", 0) >= self.thresholds["exam_heavy"]["grade_threshold"]
            ),
            "keyword_count": exam_count,
            "keyword_threshold": self.thresholds["exam_heavy"]["keyword_threshold"],
            "grade_percentage": grade_distribution.get("exam", 0),
            "grade_threshold": self.thresholds["exam_heavy"]["grade_threshold"]
        }
        
        # Assignment heavy reasoning
        reasoning["assignment_heavy"] = {
            "is_tagged": (
                assignment_count >= self.thresholds["assignment_heavy"]["keyword_threshold"] or
                grade_distribution.get("assignment", 0) >= self.thresholds["assignment_heavy"]["grade_threshold"]
            ),
            "keyword_count": assignment_count,
            "keyword_threshold": self.thresholds["assignment_heavy"]["keyword_threshold"],
            "grade_percentage": grade_distribution.get("assignment", 0),
            "grade_threshold": self.thresholds["assignment_heavy"]["grade_threshold"]
        }
        
        # Prerequisite reasoning
        reasoning["needs_prerequisite"] = {
            "is_tagged": prereq_info["has_prerequisites"],
            "keyword_count": prereq_info["count"],
            "keyword_threshold": self.thresholds["needs_prerequisite"]["keyword_threshold"],
            "courses_found": prereq_info["courses"]
        }
        
        # Attendance reasoning
        reasoning["attendance_required"] = {
            "is_tagged": attendance_strength >= self.thresholds["attendance_required"]["policy_strength"],
            "policy_strength": attendance_strength,
            "strength_threshold": self.thresholds["attendance_required"]["policy_strength"],
            "keyword_count": self.count_keyword_occurrences(syllabus_text, "attendance_required"),
            "keyword_threshold": self.thresholds["attendance_required"]["keyword_threshold"]
        }
        
        return reasoning

# PDF processing functions
def extract_text_from_pdf_pypdf(pdf_file):
    """Extract text from PDF using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text with PyPDF2: {str(e)}")
        return None

def extract_text_from_pdf_pdfminer(pdf_file):
    """Extract text from PDF using pdfminer."""
    try:
        # Create a bytes buffer from the uploaded file
        pdf_bytes = pdf_file.getvalue()
        text = extract_text(io.BytesIO(pdf_bytes))
        return text
    except Exception as e:
        st.error(f"Error extracting text with pdfminer: {str(e)}")
        return None

def extract_text_from_pdf(pdf_file):
    """Try multiple PDF extraction methods."""
    # Try pdfminer first
    text = extract_text_from_pdf_pdfminer(pdf_file)
    
    # If pdfminer fails, try PyPDF2
    if not text or len(text.strip()) == 0:
        text = extract_text_from_pdf_pypdf(pdf_file)
        
    return text
'''
# Streamlit app
def main():
    st.title("Syllabus Tagger")
    st.write("Upload a syllabus PDF to automatically generate tags.")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        # Extract text from PDF
        with st.spinner("Extracting text from PDF..."):
            syllabus_text = extract_text_from_pdf(uploaded_file)
            
        if syllabus_text and len(syllabus_text.strip()) > 0:
            # Display extracted text (collapsible)
            with st.expander("View Extracted Text"):
                st.text_area("Extracted Text", syllabus_text, height=300)
            
            # Initialize tagger and generate tags
            with st.spinner("Analyzing syllabus and generating tags..."):
                tagger = SyllabusTagger()
                tags = tagger.generate_tags(syllabus_text)
                reasoning = tagger.get_tag_reasoning(syllabus_text)
            
            # Display tags with emojis
            st.subheader("Generated Tags")
            
            tag_emojis = {
                "project_heavy": "🏗️",
                "exam_heavy": "📝",
                "assignment_heavy": "📚",
                "needs_prerequisite": "🔄",
                "attendance_required": "📅"
            }
            
            tag_descriptions = {
                "project_heavy": "This course has a significant project component",
                "exam_heavy": "This course places emphasis on exams and quizzes",
                "assignment_heavy": "This course has many assignments/homework",
                "needs_prerequisite": "This course requires prerequisite knowledge",
                "attendance_required": "This course has mandatory attendance"
            }
            
            # Display tags in a grid
            col1, col2 = st.columns(2)
            
            for i, (tag, value) in enumerate(tags.items()):
                if value:
                    display_tag = tag.replace('_', ' ').title()
                    emoji = tag_emojis.get(tag, "")
                    description = tag_descriptions.get(tag, "")
                    
                    if i % 2 == 0:
                        with col1:
                            st.success(f"**{emoji} {display_tag}**: {description}")
                    else:
                        with col2:
                            st.success(f"**{emoji} {display_tag}**: {description}")
            
            # Show detailed reasoning
            with st.expander("View Analysis Details"):
                for tag, details in reasoning.items():
                    display_tag = tag.replace('_', ' ').title()
                    st.write(f"**{display_tag}**")
                    
                    if details["is_tagged"]:
                        st.write("This tag has been applied")
                    else:
                        st.write("This tag was not applied")
                        
                    # Create a smaller table for each tag's details
                    detail_data = {}
                    for key, value in details.items():
                        if key != "is_tagged":
                            display_key = key.replace('_', ' ').title()
                            # Format courses found as a string if it's a list
                            if key == "courses_found" and isinstance(value, list):
                                if value:
                                    value = ", ".join(value)
                                else:
                                    value = "None found"
                            detail_data[display_key] = [value]
                    
                    st.table(detail_data)
                    st.write("---")
                
        else:
            st.error("Could not extract text from the PDF. Please make sure it's a text-based PDF and not just scanned images.")

if __name__ == "__main__":
    main()'
    '''