import streamlit as st
import pandas as pd
import os
from sentence_transformers import SentenceTransformer
import chromadb
import requests
import re
from functools import lru_cache

# Configure page
st.set_page_config(page_title="Course Recommender", layout="wide")

# Job-to-major mapping
job_to_major = {
    'IT': ['Computer Science', 'Computational science and engineering', 'Electrical and Computer Engineering', 'Mathematics'],
    'Software Engineer': ['Computer Science', 'Computational science and engineering', 'Electrical and Computer Engineering', 'Mathematics'],
    'Data Scientist': ['Computer Science', 'Mathematics', 'Economics', 'Physics', 'Computational science and engineering'],
    'Cybersecurity Analyst': ['Computer Science', 'Electrical and Computer Engineering', 'Public Policy'],
    'Business Analyst': ['Business Administration', 'Information Systems Management', 'Mathematics', 'Economics'],
    'Project Manager': ['Business Administration', 'Industrial Engineering', 'Systems Engineering'],
    'Machine Learning Engineer': ['Computer Science', 'Mathematics', 'Electrical and Computer Engineering', 'Computational science and engineering'],
    'Web Developer': ['Computer Science', 'Human-Computer Interaction', 'Digital Media'],
    'DevOps Engineer': ['Computer Science', 'Information Technology', 'Systems Engineering'],
    'Database Administrator': ['Computer Science', 'Information Systems', 'Information Technology'],
    'Network Engineer': ['Computer Science', 'Electrical and Computer Engineering', 'Information Technology'],
    'Cloud Architect': ['Computer Science', 'Information Technology', 'Systems Engineering'],
    'Product Manager': ['Business Administration', 'Computer Science', 'Industrial Design'],
    'UX/UI Designer': ['Human-Computer Interaction', 'Digital Media', 'Psychology', 'Industrial Design'],
    'Biomedical Engineer': ['Biomedical Engineering', 'Electrical and Computer Engineering', 'Mechanical Engineering'],
    'Financial Analyst': ['Finance', 'Economics', 'Mathematics', 'Business Administration'],
    'Marketing Analyst': ['Marketing', 'Business Administration', 'Analytics'],
    'Civil Engineer': ['Civil Engineering', 'Environmental Engineering'],
    'Mechanical Engineer': ['Mechanical Engineering', 'Aerospace Engineering'],
    'Electrical Engineer': ['Electrical and Computer Engineering', 'Physics']
}

# Course prefix to major mapping
prefix_to_major = {
    'CS': 'Computer Science',
    'CSE': 'Computational science and engineering',
    'ECE': 'Electrical and Computer Engineering',
    'MATH': 'Mathematics',
    'ECON': 'Economics',
    'PHYS': 'Physics',
    'PUBP': 'Public Policy',
    'MGT': 'Business Administration',
    'ISYE': 'Industrial Engineering',
    'SYE': 'Systems Engineering',
    'HCI': 'Human-Computer Interaction',
    'DM': 'Digital Media',
    'IT': 'Information Technology',
    'IS': 'Information Systems',
    'BMED': 'Biomedical Engineering',
    'ME': 'Mechanical Engineering',
    'FIN': 'Finance',
    'MKTG': 'Marketing',
    'CE': 'Civil Engineering',
    'ENVE': 'Environmental Engineering',
    'AE': 'Aerospace Engineering',
    'CX': 'Computational Science',
    'CYBR': 'Cybersecurity',
    'ID': 'Industrial Design',
    'PSYC': 'Psychology',
    'ACCT': 'Accounting',
    'CP': 'City Planning'
}

# Function to get absolute path relative to the script location
def get_abs_path(relative_path):
    return os.path.expanduser(relative_path)

@st.cache_resource
def load_embedding_model():
    # Load and return the embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

@st.cache_resource
def setup_vector_db():
    # Set up ChromaDB client
    client = chromadb.PersistentClient(path=get_abs_path("~/chroma_db"))
    return client

@st.cache_data
def load_datasets(jobskills_path, gt_courses_path, moocs_path):
    datasets = {}
    paths = {
        "jobskills": jobskills_path,
        "gt_courses": gt_courses_path,
        "moocs": moocs_path
    }
    
    for key, path in paths.items():
        path = get_abs_path(path)
        if os.path.exists(path):
            try:
                if key == "gt_courses":
                    datasets[key] = pd.read_csv(path, sep=';', on_bad_lines='skip', engine='python')
                else:
                    datasets[key] = pd.read_csv(path)
                st.success(f"Loaded {key} data from {path}")
            except Exception as e:
                st.warning(f"Could not load {key} data: {str(e)}")
        else:
            st.warning(f"{key} path does not exist: {path}")
    
    return datasets

def extract_skills_ollama(job_title, job_description):
    """Extract skills using locally hosted Ollama API"""
    API_URL = st.session_state.get("llm_api_url", "http://localhost:11434/api/generate")
    
    prompt = f"""You are a career skills expert with deep knowledge of technical fields.

Task: Analyze this job description for a {job_title} role and extract the top 7-10 most important technical skills required.

Job Description:
{job_description}

Instructions:
1. Focus on hard technical skills, technologies, tools, languages, frameworks, or domain knowledge
2. DO NOT include soft skills (communication, teamwork, etc.)
3. Extract ONLY the skills that are explicitly mentioned or clearly implied
4. Format your response as a comma-separated list with no other text
5. If a skill has multiple names (e.g. "Machine Learning/ML"), choose the most commonly used term
6. Identify the industry field as well and suggested appropriate courses.

Example output format: Python, SQL, TensorFlow, data visualization, cloud computing, Docker, CI/CD

Skills:"""

    try:
        payload = {
            "model": st.session_state.get("llm_model_name", "llama3.2"),
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1
        }
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        
        skills_text = response.json()["response"].strip()
        skills_list = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
        
        return skills_list
    except Exception as e:
        st.error(f"LLM API Error: {str(e)}")
        return []

def extract_skills_gemini(job_title, job_description):
    """Extract skills using Google's Gemini API"""
    import google.generativeai as genai
    
    # Setup the API with your key (store this securely)
    # Get your API key from https://aistudio.google.com/app/apikey
    if "api_key" not in st.session_state:
        st.error("Please enter your Gemini API key in settings")
        return []
        
    genai.configure(api_key=st.session_state.get("api_key"))
    
    # Create a model instance
    model = genai.GenerativeModel(
        model_name=st.session_state.get("llm_model_name", "models/gemini-1.5-pro-latest"),
        generation_config={
            "temperature": 0.1,
            "max_output_tokens": 250,
        }
    )
    
    prompt = f"""You are an academic advisor at Georgia Tech with deep knowledge of technical fields and the courses offered.

Task: Analyze this job description for a {job_title} role and:
1. Extract the top 5-7 most important technical skills required which could be actual subjects. For example, for a cloud related role, operating systems and computer networks are required courses. 
2. Identify which Georgia Tech majors are most relevant for this role
3. Suggest 3-5 specific Georgia Tech courses (with course IDs) that would help develop these skills

Job Description:
{job_description}

Instructions:
1. Focus on hard technical skills, technologies, tools, languages, frameworks, or domain knowledge
2. DO NOT include soft skills (communication, teamwork, etc.)
3. Format your response as follows:

Skills: [comma-separated list of skills]
Relevant Majors: [comma-separated list of majors]
Recommended GT Courses: [Course ID 1]: [Course Name 1], [Course ID 2]: [Course Name 2], etc.
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract just the skills list
        skills_text = ""
        if "Skills:" in response_text:
            skills_section = response_text.split("Skills:")[1].split("Relevant Majors:")[0].strip()
            skills_text = skills_section
        
        skills_list = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
        
        # Also capture recommended courses for reference
        gt_course_recommendations = []
        if "Recommended GT Courses:" in response_text:
            courses_section = response_text.split("Recommended GT Courses:")[1].strip()
            gt_course_recommendations = courses_section.split(",")
        
        # Store LLM-recommended courses for later reference
        st.session_state["llm_gt_recommendations"] = gt_course_recommendations
        
        return skills_list
    except Exception as e:
        st.error(f"Gemini API Error: {str(e)}")
        return []
def extract_skills_together(job_title, job_description):
    """Extract skills using Together.ai API"""
    API_URL = "https://api.together.xyz/v1/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.get('api_key', '')}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are a career skills expert with deep knowledge of technical fields.

Task: Analyze this job description for a {job_title} role and extract the top 7-10 most important technical skills required.

Job Description:
{job_description}

Instructions:
1. Focus on hard technical skills, technologies, tools, languages, frameworks, or domain knowledge
2. DO NOT include soft skills (communication, teamwork, etc.)
3. Extract ONLY the skills that are explicitly mentioned or clearly implied
4. Format your response as a comma-separated list with no other text
5. If a skill has multiple names (e.g. "Machine Learning/ML"), choose the most commonly used term
6. Identify the industry field as well and suggested appropriate courses.

Example output format: Python, SQL, TensorFlow, data visualization, cloud computing, Docker, CI/CD

Skills:"""

    try:
        payload = {
            "model": st.session_state.get("llm_model_name", "togethercomputer/llama-2-7b-chat"),
            "prompt": prompt,
            "max_tokens": 100,
            "temperature": 0.1
        }
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        skills_text = response.json()["choices"][0]["text"].strip()
        skills_list = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
        
        return skills_list
    except Exception as e:
        st.error(f"Together API Error: {str(e)}")
        return []

def extract_skills_deepseek(job_title, job_description):
    """Extract skills using DeepSeek API"""
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.session_state.get('api_key', '')}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are a career skills expert with deep knowledge of technical fields.

Task: Analyze this job description for a {job_title} role and extract the top 7-10 most important technical skills required.

Job Description:
{job_description}

Instructions:
1. Focus on hard technical skills, technologies, tools, languages, frameworks, or domain knowledge
2. DO NOT include soft skills (communication, teamwork, etc.)
3. Extract ONLY the skills that are explicitly mentioned or clearly implied
4. Format your response as a comma-separated list with no other text
5. If a skill has multiple names (e.g. "Machine Learning/ML"), choose the most commonly used term
6. Identify the industry field as well and suggested appropriate courses.
7. Give 3-7 courses offered from Georgia Tech along with course ID for courses offered which are relevant to the skills identified.

Example output format: Python, SQL, TensorFlow, data visualization, cloud computing, Docker, CI/CD"""

    try:
        payload = {
            "model": st.session_state.get("llm_model_name", "deepseek-chat"),
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 100
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        skills_text = response.json()["choices"][0]["message"]["content"].strip()
        skills_list = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
        
        return skills_list
    except Exception as e:
        st.error(f"DeepSeek API Error: {str(e)}")
        return []

def extract_skills(job_title, job_description, api_type="ollama"):
    """Extract skills using the selected API method"""
    if api_type == "ollama":
        return extract_skills_ollama(job_title, job_description)
    elif api_type == "together":
        return extract_skills_together(job_title, job_description)
    elif api_type == "deepseek":
        return extract_skills_deepseek(job_title, job_description)
    elif api_type=="gemini":
        return extract_skills_gemini(job_title, job_description)
    else:
        st.error(f"Unknown API type: {api_type}")
        return []
# New helper functions for advanced recommendation system

def fallback_skill_extraction(job_description):
    """Extract potential skills using keyword analysis when LLM extraction fails"""
    # Common technical skills to look for
    common_skills = [
        "python", "java", "javascript", "c++", "sql", "nosql", "aws", "azure", 
        "docker", "kubernetes", "machine learning", "deep learning", "data analysis",
        "visualization", "tensorflow", "pytorch", "nlp", "computer vision", "agile",
        "cloud", "devops", "ci/cd", "git", "data science", "statistics", "r programming",
        "big data", "hadoop", "spark", "tableau", "power bi", "excel", "web development",
        "mobile development", "api", "microservices", "security", "networking", "linux",
        "windows", "databases", "data engineering", "etl", "analytics", "full stack"
    ]
    
    # Find matches
    job_desc_lower = job_description.lower()
    found_skills = []
    
    # Check for skills
    for skill in common_skills:
        if re.search(rf'\b{re.escape(skill)}\b', job_desc_lower):
            found_skills.append(skill)
    
    st.write("Extracted Skills (fallback method):", found_skills)
    return found_skills

def normalize_skills(skills):
    """
    Normalize extracted skills to handle variations and synonyms
    """
    # Define common variations and synonyms
    skill_mappings = {
        "python programming": "python",
        "python coding": "python",
        "ml": "machine learning",
        "tensorflow": "tensorflow/keras",
        "pytorch": "pytorch",
        "artificial intelligence": "machine learning",
        "visualization": "data visualization",
        "postgresql": "sql",
        "mysql": "sql",
        "database": "databases",
        "cloud computing": "cloud",
        "aws cloud": "aws",
        "amazon web services": "aws",
        "azure cloud": "azure",
        "google cloud": "gcp",
        "software development": "software engineering",
        "javascript": "js/javascript",
        "js": "js/javascript",
        "react": "react/frontend",
        "ui/ux": "ux design",
        "statistics": "statistics/math",
        "mathematical": "statistics/math",
        "deep learning": "deep learning/neural networks",
        "nn": "deep learning/neural networks",
        "data analytics": "data analysis",
        "nlp": "natural language processing",
        "cv": "computer vision",
        "ci/cd": "devops/ci/cd",
        "linux": "linux/unix",
        "unix": "linux/unix",
    }
    
    # Clean and normalize skills
    normalized_skills = []
    seen_skills = set()
    
    for skill in skills:
        skill_lower = skill.lower().strip()
        
        # Apply mappings if they exist
        normalized_skill = skill_mappings.get(skill_lower, skill_lower)
        
        # Avoid duplicates
        if normalized_skill not in seen_skills:
            normalized_skills.append(normalized_skill)
            seen_skills.add(normalized_skill)
    
    return normalized_skills

def weight_skills(skills, job_title, job_description):
    """
    Weight skills based on their importance in the job description
    """
    weighted_skills = []
    job_title_lower = job_title.lower()
    job_desc_lower = job_description.lower()
    
    for skill in skills:
        # Base weight
        weight = 1.0
        
        # If skill appears in title, it's more important
        if skill.lower() in job_title_lower:
            weight += 0.5
            
        # Count occurrences in description
        skill_occurrences = job_desc_lower.count(skill.lower())
        # More occurrences suggest higher importance
        if skill_occurrences > 1:
            weight += min(0.3, skill_occurrences * 0.1)  # Cap at +0.3
            
        # Check if skill appears early in description (likely more important)
        first_paragraph = job_desc_lower.split("\n")[0]
        if skill.lower() in first_paragraph:
            weight += 0.2
            
        weighted_skills.append({"skill": skill, "weight": min(2.0, weight)})  # Cap at 2.0
    
    # Sort by weight
    weighted_skills.sort(key=lambda x: x["weight"], reverse=True)
    
    return weighted_skills
# Function to map job title to relevant majors
def get_relevant_majors(job_title):
    """
    Map job title to relevant majors using the job_to_major dictionary
    """
    # Normalize job title for matching
    job_title_lower = job_title.lower().strip()
    
    # Direct match
    for job, majors in job_to_major.items():
        if job.lower() == job_title_lower:
            return majors
    
    # Partial match
    for job, majors in job_to_major.items():
        if job.lower() in job_title_lower or job_title_lower in job.lower():
            return majors
    
    # Default to a broad set of technical majors if no match found
    return ['Computer Science', 'Mathematics', 'Business Administration', 'Information Technology']

# Function to check if a course belongs to a relevant major
def is_relevant_major_course(course_id, relevant_majors):
    """
    Check if a course belongs to one of the relevant majors based on course ID prefix
    """
    if not course_id or not isinstance(course_id, str):
        return False
        
    parts = course_id.split()
    if len(parts) < 1:
        return False
        
    prefix = parts[0]
    major = prefix_to_major.get(prefix)
    
    if not major:
        return False
        
    return major in relevant_majors

# Enhanced skill extraction that combines LLM extraction with user-provided skills
def enhanced_skill_extraction(job_title, job_description, user_skills=None, api_type="gemini"):
    """
    Extract skills using the selected API method and combine with user-provided skills
    """
    # Get skills from LLM
    extracted_skills = extract_skills(job_title, job_description, api_type)
    
    # If LLM extraction failed, use fallback
    if not extracted_skills:
        extracted_skills = fallback_skill_extraction(job_description)
    
    # Include user-provided skills if any
    if user_skills:
        if isinstance(user_skills, str):
            user_skills = [s.strip() for s in user_skills.split(',')]
        
        # Add user skills to extracted skills, avoiding duplicates
        for skill in user_skills:
            if skill and skill.strip() and skill.strip().lower() not in [s.lower() for s in extracted_skills]:
                extracted_skills.append(skill.strip())
    
    # Normalize the combined skills
    normalized_skills = normalize_skills(extracted_skills)
    
    # Limit to reasonable number (prioritizing user skills)
    return normalized_skills[:10]

def initialize_vector_database(datasets, embedding_model):
    client = setup_vector_db()
    
    # Create or get collections for our datasets
    try:
        # Get existing collection names
        existing_collection_names = client.list_collections()
        
        st.write(f"Existing collections: {existing_collection_names}")
        
        # Georgia Tech courses collection
        if "gt_courses" not in existing_collection_names and "gt_courses" in datasets:
            gt_collection = client.create_collection(name="gt_courses")
            gt_df = datasets["gt_courses"]
            
            # Process in smaller batches
            batch_size = 500  # Smaller batch size for safety
            total_rows = len(gt_df)
            
            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = gt_df.iloc[start_idx:end_idx]
                
                # Prepare batch data
                documents = batch_df["Description"].fillna("").tolist()
                ids = [f"gt_{i}" for i in range(start_idx, end_idx)]
                metadatas = batch_df[["Course ID", "Course Name"]].to_dict('records')
                
                # Generate embeddings for batch
                embeddings = embedding_model.encode(documents)
                embeddings_list = [emb.tolist() for emb in embeddings]
                
                # Log batch size
                st.write(f"GT Courses - Initializing batch {start_idx}-{end_idx}: {len(embeddings_list)} embeddings")
                
                # Add batch to collection
                gt_collection.add(
                    embeddings=embeddings_list,
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                
                # Show progress
                progress = min(100, int((end_idx / total_rows) * 100))
                st.progress(progress / 100)
                
            st.success(f"Georgia Tech courses vectorized and stored ({total_rows} items)")
        elif "gt_courses" in existing_collection_names:
            st.info("Georgia Tech courses collection already exists")
        
        # MOOCs collection - also process in smaller batches
        if "moocs" not in existing_collection_names and "moocs" in datasets:
            mooc_collection = client.create_collection(name="moocs")
            mooc_df = datasets["moocs"]
            
            # Process in smaller batches
            batch_size = 250  # Significantly smaller batch size for MOOCs
            total_rows = len(mooc_df)
            
            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = mooc_df.iloc[start_idx:end_idx]
                
                # Prepare batch data
                documents = batch_df["About"].fillna("").tolist()
                ids = [f"mooc_{i}" for i in range(start_idx, end_idx)]
                metadatas = batch_df[["Name", "Link"]].to_dict('records')
                
                # Generate embeddings for batch
                embeddings = embedding_model.encode(documents)
                embeddings_list = [emb.tolist() for emb in embeddings]
                
                # Log batch size
                st.write(f"MOOCs - Initializing batch {start_idx}-{end_idx}: {len(embeddings_list)} embeddings")
                
                # Add batch to collection
                mooc_collection.add(
                    embeddings=embeddings_list,
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                
                # Show progress
                progress = min(100, int((end_idx / total_rows) * 100))
                st.progress(progress / 100)
                
            st.success(f"MOOC courses vectorized and stored ({total_rows} items)")
        elif "moocs" in existing_collection_names:
            st.info("MOOCs collection already exists")
            
        return True
    except Exception as e:
        st.error(f"Error initializing vector database: {str(e)}")
        # Print more detailed error information
        import traceback
        st.code(traceback.format_exc())
        return False
def refresh_vector_database(datasets, embedding_model):
    client = setup_vector_db()
    
    # Get existing collection names - FIXED LINE
    existing_collection_names = client.list_collections()
    st.write(f"Existing collections: {existing_collection_names}")

    try:
        # Handle GT courses collection refresh
        if "gt_courses" in datasets:
            if "gt_courses" in existing_collection_names:
                # Get the collection and delete all existing data
                gt_collection = client.get_collection(name="gt_courses")
                all_ids = gt_collection.get()["ids"]
                if all_ids:
                    gt_collection.delete(ids=all_ids)
                st.warning("Deleted existing GT courses data for refresh")
            else:
                # Create new collection if it doesn't exist
                gt_collection = client.create_collection(name="gt_courses")
                
            # Process the GT courses data
            gt_df = datasets["gt_courses"]
            
            # Process in smaller batches for GT courses
            batch_size = 500  # Reduced batch size for safety
            total_rows = len(gt_df)
            
            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = gt_df.iloc[start_idx:end_idx]
                
                # Prepare batch data
                documents = batch_df["Description"].fillna("").tolist()
                ids = [f"gt_{i}" for i in range(start_idx, end_idx)]
                metadatas = batch_df[["Course ID", "Course Name"]].to_dict('records')
                
                # Generate embeddings for batch
                embeddings = embedding_model.encode(documents)
                embeddings_list = [emb.tolist() for emb in embeddings]
                
                # Log the batch size for debugging
                st.write(f"GT Courses - Processing batch {start_idx}-{end_idx}: {len(embeddings_list)} embeddings")
                
                # Add batch to collection
                gt_collection.add(
                    embeddings=embeddings_list,
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                
                # Show progress
                progress = min(100, int((end_idx / total_rows) * 100))
                st.progress(progress / 100)
                
            st.success(f"Georgia Tech courses refreshed and stored ({total_rows} items)")
        
        # Handle MOOCs collection refresh
        if "moocs" in datasets:
            if "moocs" in existing_collection_names:
                # Get the collection and delete all existing data
                mooc_collection = client.get_collection(name="moocs")
                # Get all document IDs
                all_ids = mooc_collection.get()["ids"]
                if all_ids:
                    # Delete in batches to avoid exceeding the limit
                    BATCH_SIZE = 5461  # maximum allowed batch size
                    for i in range(0, len(all_ids), BATCH_SIZE):
                        batch_ids = all_ids[i:i+BATCH_SIZE]
                        mooc_collection.delete(ids=batch_ids)
                        st.write(f"Deleted MOOCs batch from index {i} to {i + len(batch_ids)}")
                    st.warning("Deleted existing MOOCs data for refresh")
            else:
                # Create new collection if it doesn't exist
                mooc_collection = client.create_collection(name="moocs")
                        
            # Process the MOOCs data
            mooc_df = datasets["moocs"]
                    
            # Process in even smaller batches for MOOCs
            batch_size = 1000  # Significantly reduced batch size for MOOCs
            total_rows = len(mooc_df)
                    
            for start_idx in range(0, total_rows, batch_size):
                end_idx = min(start_idx + batch_size, total_rows)
                batch_df = mooc_df.iloc[start_idx:end_idx]
                        
                # Prepare batch data
                documents = batch_df["About"].fillna("").tolist()
                ids = [f"mooc_{i}" for i in range(start_idx, end_idx)]
                metadatas = batch_df[["Name", "Link"]].to_dict('records')
                        
                # Generate embeddings for batch
                embeddings = embedding_model.encode(documents)
                embeddings_list = [emb.tolist() for emb in embeddings]
                        
                # Log the batch size for debugging
                st.write(f"MOOCs - Processing batch {start_idx}-{end_idx}: {len(embeddings_list)} embeddings")
                        
                # Add batch to collection - make sure we're only submitting the current batch
                mooc_collection.add(
                    embeddings=embeddings_list,
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                        
                # Show progress
                progress = min(100, int((end_idx / total_rows) * 100))
                st.progress(progress / 100)
            
            st.success(f"MOOCs refreshed and stored ({total_rows} items)")
            
        return True
    except Exception as e:
        st.error(f"Error refreshing vector database: {str(e)}")
        # Print more detailed error information
        import traceback
        st.code(traceback.format_exc())
        return False
# Improved direct_search function with better matching and skill weights
def improved_direct_search(datasets, weighted_skills, dataset_key):
    """Perform direct keyword search on the dataset with improved relevance"""
    results = []
    
    if dataset_key not in datasets:
        return results
        
    df = datasets[dataset_key]
    
    # Support empty dataframe
    if df is None or len(df) == 0:
        return results
    
    skills = [item["skill"] for item in weighted_skills]
    skill_weights = {item["skill"]: item["weight"] for item in weighted_skills}
    
    # Define which fields to search based on dataset type
    if dataset_key == "gt_courses":
        search_fields = ["Course Name", "Description"]
        metadata_fields = ["Course ID", "Course Name"]
        description_field = "Description"
        # Domain filtering - expanded to include more domains
        tech_domains = ["CS", "CSE", "ECE", "CX", "ISYE", "CP", "MGT", "CYBR"]
        data_domains = ["CSE", "ISYE", "CS"]
        ml_domains = ["CS", "CSE", "ISYE"]
    elif dataset_key == "moocs":
        search_fields = ["Name", "About"]
        metadata_fields = ["Name", "Link"]
        description_field = "About"
    else:
        return results
    
    # Search for each skill in the relevant fields
    for skill_item in weighted_skills:
        skill = skill_item["skill"]
        skill_weight = skill_item["weight"]
        skill_lower = skill.lower()
        
        # Create a mask for rows that contain the skill
        mask = False
        for field in search_fields:
            if field in df.columns:
                # More precise word boundary matching
                field_mask = df[field].fillna("").str.lower().str.contains(
                    r'\b' + re.escape(skill_lower) + r'\b', 
                    na=False, 
                    regex=True
                )
                mask = mask | field_mask
        
        # Get matching rows
        matches = df[mask]
        
        # Apply domain filtering 
        if dataset_key == "gt_courses":
            # Extract course prefix
            if "Course ID" in matches.columns:
                matches["course_prefix"] = matches["Course ID"].str.split(" ", n=1).str[0]
                
                # Apply different domain boosts based on skill type
                if skill_lower in ["aws", "cloud", "python", "docker", "kubernetes", "linux", "programming"]:
                    matches["domain_boost"] = matches["course_prefix"].apply(
                        lambda prefix: 0.4 if prefix in tech_domains else 0
                    )
                elif skill_lower in ["data science", "data analysis", "data visualization", "statistics"]:
                    matches["domain_boost"] = matches["course_prefix"].apply(
                        lambda prefix: 0.35 if prefix in data_domains else 0
                    )
                elif skill_lower in ["machine learning", "deep learning", "neural networks", "ai"]:
                    matches["domain_boost"] = matches["course_prefix"].apply(
                        lambda prefix: 0.35 if prefix in ml_domains else 0
                    )
                else:
                    matches["domain_boost"] = 0
            else:
                matches["domain_boost"] = 0
        else:
            matches["domain_boost"] = 0
        
        # Calculate scores with skill weight factored in
        for _, row in matches.iterrows():
            # Base score starts lower but considers skill weight
            base_score = 0.4 * skill_weight
            
            # Add domain boost
            score = base_score + row.get("domain_boost", 0)
            
            # Title/Name field match importance
            for field in search_fields:
                if field in df.columns:
                    field_value = str(row.get(field, "")).lower()
                    
                    # Course name/title match is worth more
                    if field in ["Course Name", "Name"]:
                        # Exact word boundary match
                        if re.search(rf'\b{re.escape(skill_lower)}\b', field_value):
                            score += 0.4 * skill_weight
                        # Partial match still valuable
                        elif skill_lower in field_value:
                            score += 0.2 * skill_weight
                    
                    # Description match with improved weighting
                    elif field in ["Description", "About"]:
                        # Count occurrences with word boundaries
                        occurrences = len(re.findall(rf'\b{re.escape(skill_lower)}\b', field_value))
                        if occurrences > 0:
                            # More occurrences indicate stronger relevance
                            score += min(0.3, 0.1 * occurrences) * skill_weight
            
            # Only include results above threshold
            if score >= 0.65:
                result = {
                    "Score": min(1.0, score),
                    "Match Type": "Direct Match",
                    "Matching Skills": [skill],
                    "Skill Weight": skill_weight,
                    "Description": str(row.get(description_field, ""))
                }
                
                # Add metadata fields
                for field in metadata_fields:
                    if field in df.columns:
                        result[field] = row.get(field, "")
                
                # Add course level info if available
                if dataset_key == "gt_courses" and "Course ID" in result:
                    # Extract course number to estimate level
                    course_id_parts = result["Course ID"].split(" ")
                    if len(course_id_parts) > 1:
                        try:
                            course_num = int(course_id_parts[1][0])  # First digit of course number
                            # Undergraduate vs graduate heuristic
                            result["Course Level"] = "Graduate" if course_num >= 6 else "Undergraduate"
                        except:
                            result["Course Level"] = "Unknown"
                
                results.append(result)
    
    return results
# Improved semantic search function with better query construction
def improved_semantic_search(datasets, weighted_skills, job_title, dataset_key, embedding_model):
    """Perform semantic search with improved query construction"""
    results = []
    
    try:
        # Check for empty dataset
        if dataset_key not in datasets or datasets[dataset_key] is None or len(datasets[dataset_key]) == 0:
            return results
            
        # Extract just the skills for processing
        skills = [item["skill"] for item in weighted_skills]
        skill_weights = {item["skill"]: item["weight"] for item in weighted_skills}
        
        # Build a better query that emphasizes high-weight skills
        top_skills = sorted(weighted_skills, key=lambda x: x["weight"], reverse=True)[:5]
        primary_skills = [item["skill"] for item in top_skills]
        
        # More targeted query construction
        query_parts = []
        query_parts.append(f"Courses for {job_title}")
        query_parts.append(f"Skills needed: {', '.join(primary_skills)}")
        
        # Add skill-specific context based on top skills
        for skill in primary_skills[:3]:  # Just use top 3 to avoid query dilution
            if "python" in skill.lower():
                query_parts.append("Python programming language courses")
            elif "machine learning" in skill.lower() or "ai" in skill.lower():
                query_parts.append("Machine learning and artificial intelligence courses")
            elif "data" in skill.lower() and ("science" in skill.lower() or "analysis" in skill.lower()):
                query_parts.append("Data science and analysis courses")
            elif "cloud" in skill.lower() or "aws" in skill.lower() or "azure" in skill.lower():
                query_parts.append("Cloud computing and infrastructure courses")
            elif "web" in skill.lower() or "frontend" in skill.lower() or "javascript" in skill.lower():
                query_parts.append("Web development courses")
        
        # Construct final query
        query_text = " ".join(query_parts)
        
        # Get vector DB client and relevant collection
        client = setup_vector_db()
        collection_names = client.list_collections()
        
        if dataset_key not in collection_names:
            return results
            
        collection = client.get_collection(dataset_key)
        
        # Generate query embedding
        query_embedding = embedding_model.encode(query_text).tolist()
        
        # Get more results initially for better filtering
        n_results = min(20, max(7, len(skills) * 3))
        
        # Query the collection
        query_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Process results
        if query_results and len(query_results['ids']) > 0 and len(query_results['ids'][0]) > 0:
            for i in range(len(query_results['ids'][0])):
                # Base score with less steep drop-off by rank
                score = 0.82 - (i * 0.02)
                
                doc = query_results['documents'][0][i]
                metadata = query_results['metadatas'][0][i]
                
                # Find which skills match this result
                matching_skills = []
                total_skill_weight = 0
                for skill in skills:
                    # Using more precise word boundary matching
                    if re.search(rf'\b{re.escape(skill.lower())}\b', doc.lower()):
                        matching_skills.append(skill)
                        # Add weighted score based on skill importance
                        weight = skill_weights.get(skill, 1.0)
                        score += 0.05 * weight
                        total_skill_weight += weight
                
                # Add skill weight factor to score
                if total_skill_weight > 0:
                    # Normalize by number of matching skills to avoid bias toward courses that match many low-weight skills
                    avg_skill_weight = total_skill_weight / len(matching_skills) if matching_skills else 0
                    score += min(0.15, avg_skill_weight * 0.1)
                
                # Domain relevance check for GT courses
                if dataset_key == "gt_courses" and "Course ID" in metadata:
                    course_id = metadata["Course ID"]
                    course_prefix = course_id.split(" ")[0] if " " in course_id else ""
                    
                    # Computer Science courses for programming skills
                    if any(s.lower() in ["python", "programming", "software engineering", "coding"] for s in matching_skills):
                        if course_prefix in ["CS", "CSE"]:
                            score += 0.15
                    
                    # Data science related courses
                    if any(s.lower() in ["data science", "data analysis", "statistics"] for s in matching_skills):
                        if course_prefix in ["ISYE", "CSE", "CS"]:
                            score += 0.15
                    
                    # Extract course level
                    try:
                        if " " in course_id:
                            course_num = int(course_id.split(" ")[1][0])  # First digit 
                            course_level = "Graduate" if course_num >= 6 else "Undergraduate"
                        else:
                            course_level = "Unknown"
                    except:
                        course_level = "Unknown"
                
                # Refined threshold based on matching skills
                score_threshold = 0.7
                if len(matching_skills) > 0:
                    score_threshold = 0.65
                
                if score >= score_threshold:
                    result = {
                        "Score": min(1.0, score),
                        "Match Type": "Semantic Match",
                        "Matching Skills": matching_skills,
                        "Description": doc
                    }
                    
                    # Add metadata
                    for key, value in metadata.items():
                        result[key] = value
                    
                    # Add course level for GT courses
                    if dataset_key == "gt_courses" and "Course ID" in metadata:
                        course_id_parts = metadata["Course ID"].split(" ")
                        if len(course_id_parts) > 1:
                            try:
                                course_num = int(course_id_parts[1][0])
                                result["Course Level"] = "Graduate" if course_num >= 6 else "Undergraduate"
                            except:
                                result["Course Level"] = "Unknown"
                    
                    results.append(result)
    except Exception as e:
        st.error(f"Error during semantic search: {str(e)}")
    
    return results
# This function helps combine results from direct and semantic search
def combine_results(direct_results, semantic_results, key_field):
    """Combine and deduplicate results from different search methods"""
    combined = {}
    
    # Process direct results first
    for result in direct_results:
        if key_field in result:
            key = result[key_field]
            combined[key] = result
    
    # Add or update with semantic results
    for result in semantic_results:
        if key_field in result:
            key = result[key_field]
            
            if key in combined:
                # If already exists, keep the higher score
                if result["Score"] > combined[key]["Score"]:
                    # Keep the match type and skills from both
                    combined[key]["Match Type"] = "Direct + Semantic Match"
                    combined[key]["Score"] = result["Score"]
                    
                    # Merge matching skills lists
                    existing_skills = set(combined[key].get("Matching Skills", []))
                    new_skills = set(result.get("Matching Skills", []))
                    combined[key]["Matching Skills"] = list(existing_skills.union(new_skills))
            else:
                combined[key] = result
    
    return list(combined.values())

# Advanced filtering function implementation
def advanced_filtering(results, dataset_key, weighted_skills, job_title):
    """Apply advanced filtering based on job context and course relevance"""
    filtered_results = []
    
    # Extract skills
    skills = [item["skill"] for item in weighted_skills]
    
    # Detect job level/seniority
    job_level = "entry"  # Default
    if any(term in job_title.lower() for term in ["senior", "lead", "manager", "director", "principal"]):
        job_level = "senior"
    elif any(term in job_title.lower() for term in ["mid", "intermediate", "associate"]):
        job_level = "mid"
    
    # Define tech skills that should preferentially match with tech courses
    tech_skills = ["aws", "cloud", "python", "docker", "linux", "programming", 
                   "javascript", "java", "computing", "database", "cybersecurity",
                   "kubernetes", "devops", "backend", "frontend"]
    
    # Define tech course prefixes with expanded list
    tech_prefixes = ["CS", "CSE", "ECE", "CX", "ISYE", "CP", "MGT", "CYBR", "SWE"]
    
    for result in results:
        # Default decision
        keep = True
        result_score = result["Score"]
        
        # Special filtering for GT courses
        if dataset_key == "gt_courses" and "Course ID" in result:
            course_id = result["Course ID"] 
            course_prefix = course_id.split(" ")[0] if " " in course_id else ""
            
            # For tech skills, prioritize tech courses
            if any(skill.lower() in tech_skills for skill in skills):
                if course_prefix not in tech_prefixes:
                    # Not in tech domain but high score - keep but reduce score slightly
                    if result_score > 0.85:
                        result["Score"] = result_score * 0.9
                    # Medium score and not tech domain - consider filtering
                    elif result_score < 0.8:
                        # Keep only if it has explicit skill matches
                        matching_skills = result.get("Matching Skills", [])
                        if not matching_skills:
                            keep = False
            
            # Course level matching based on job seniority
            if "Course Level" in result:
                course_level = result["Course Level"]
                
                # Senior roles should get more advanced courses
                if job_level == "senior" and course_level == "Undergraduate":
                    # Reduce score for undergraduate courses for senior roles
                    result["Score"] = result_score * 0.85
                # Entry level roles prefer undergraduate courses
                elif job_level == "entry" and course_level == "Graduate":
                    # Graduate courses still okay for entry level, but slightly less preferred
                    result["Score"] = result_score * 0.95
        
        # For MOOCs, ensure quality matches for highly specific skills
        if dataset_key == "moocs" and "Name" in result:
            course_name = result["Name"].lower()
            matching_skills = result.get("Matching Skills", [])
            
            # For very specific technical skills like AWS, look for explicit mentions
            if any(skill.lower() in ["aws", "kubernetes", "tensorflow", "pytorch"] for skill in skills):
                target_skills = [s for s in skills if s.lower() in ["aws", "kubernetes", "tensorflow", "pytorch"]]
                explicit_match = False
                
                for target in target_skills:
                    target_lower = target.lower()
                    # Check if explicitly mentioned in course name
                    if target_lower in course_name:
                        explicit_match = True
                        break
                
                # If no explicit match in course name and score is marginal
                if not explicit_match and result_score < 0.82:
                    # Look at matching skills
                    if not any(skill.lower() in target_skill.lower() for skill in matching_skills 
                              for target_skill in target_skills):
                        # No explicit match anywhere, reduce confidence
                        if result_score < 0.75:
                            keep = False
                        else:
                            result["Score"] = result_score * 0.9
        
        if keep:
            filtered_results.append(result)
    
    return filtered_results
# Main implementation for course recommendations
def implement_course_recommendations(job_title, job_description, user_skills=None, seniority_level="Mid-Level"):
    """
    Master function to generate course recommendations based on job details
    """
    if not job_description.strip():
        return "Please enter a valid job description."
    
    # Connect seniority level from UI to internal representation
    job_level_mapping = {
        "Entry-Level": "entry",
        "Mid-Level": "mid",
        "Senior": "senior"
    }
    job_level = job_level_mapping.get(seniority_level, "mid")
    
    # 1. Get relevant majors for this job
    relevant_majors = get_relevant_majors(job_title)
    st.write(f"**Relevant Majors for {job_title}:** {', '.join(relevant_majors)}")
    
    # 2. Extract and normalize skills
    normalized_skills = enhanced_skill_extraction(job_title, job_description, user_skills)
    st.write(f"**Identified Skills:** {', '.join(normalized_skills)}")
    
    # 3. Weight skills by importance
    weighted_skills = weight_skills(normalized_skills, job_title, job_description)
    
    # 4. Get datasets
    datasets = st.session_state.get("datasets", {})
    embedding_model = load_embedding_model()
    
    # 5. Filter Georgia Tech courses by relevant majors
    gt_df = datasets.get("gt_courses")
    if gt_df is not None:
        # Create a new column indicating whether the course belongs to a relevant major
        gt_df['is_relevant_major'] = gt_df['Course ID'].apply(
            lambda x: is_relevant_major_course(x, relevant_majors)
        )
        
        # Filter to only relevant major courses
        relevant_gt_df = gt_df[gt_df['is_relevant_major']]
        
        # Create a temporary dataset with only the relevant courses
        relevant_datasets = {
            "gt_courses": relevant_gt_df,
            "moocs": datasets.get("moocs")  # Keep all MOOCs for now
        }
        
        # Log the filtering results
        st.write(f"Filtered from {len(gt_df)} courses to {len(relevant_gt_df)} courses in relevant majors")
    else:
        relevant_datasets = datasets
        st.warning("GT courses dataset not available, skipping major filtering")
    
    # 6. Perform improved searches on filtered dataset
    gt_direct = improved_direct_search(relevant_datasets, weighted_skills, "gt_courses")
    gt_semantic = improved_semantic_search(relevant_datasets, weighted_skills, job_title, "gt_courses", embedding_model)
    gt_combined = combine_results(gt_direct, gt_semantic, "Course ID")
    
    # 7. Apply advanced filtering with job level consideration
    gt_filtered = advanced_filtering(gt_combined, "gt_courses", weighted_skills, job_title)
    
    # Apply additional job level weighting based on UI selection
    gt_results = []
    for course in gt_filtered:
        if "Course Level" in course:
            # Adjust scores based on seniority level
            if job_level == "entry" and course["Course Level"] == "Graduate":
                course["Score"] *= 0.9  # Downweight graduate courses for entry level
            elif job_level == "senior" and course["Course Level"] == "Undergraduate":
                course["Score"] *= 0.9  # Downweight undergraduate courses for senior level
        gt_results.append(course)
    
    # 8. For MOOCs, we can't easily filter by major, so search all MOOCs
    mooc_direct = improved_direct_search(datasets, weighted_skills, "moocs")
    mooc_semantic = improved_semantic_search(datasets, weighted_skills, job_title, "moocs", embedding_model)
    mooc_combined = combine_results(mooc_direct, mooc_semantic, "Name")
    mooc_results = advanced_filtering(mooc_combined, "moocs", weighted_skills, job_title)
    
    # 9. Group courses by skills they match
    skill_to_courses = {item["skill"]: {"gt": [], "mooc": []} for item in weighted_skills}
    
    # Add GT courses to skill groups
    for course in gt_results:
        matching_skills = course.get("Matching Skills", [])
        for skill in matching_skills:
            if skill in skill_to_courses:
                skill_to_courses[skill]["gt"].append(course)
                
    # Add MOOC courses to skill groups
    for course in mooc_results:
        matching_skills = course.get("Matching Skills", [])
        for skill in matching_skills:
            if skill in skill_to_courses:
                skill_to_courses[skill]["mooc"].append(course)
    
    # 10. Format the output
    output = f"## Course Recommendations for {job_title} ({seniority_level})\n\n"
    output += f"Based on the identified skills: **{', '.join([item['skill'] for item in weighted_skills])}**\n\n"
    
    # Add relevant majors information
    output += f"**Relevant Academic Areas:** {', '.join(relevant_majors)}\n\n"
    
    # Track courses we've already added to avoid duplicates
    added_gt_courses = set()
    added_mooc_courses = set()
    
    # Add top overall recommended courses first
    output += "### 🌟 Top Overall Recommended Courses\n\n"
    
    # Top Georgia Tech courses
    if gt_results:
        output += "#### Georgia Tech Courses:\n\n"
        top_gt = sorted(gt_results, key=lambda x: -x["Score"])[:5]
        for course in top_gt:
            course_id = course["Course ID"]
            added_gt_courses.add(course_id)
            
            # Add course level information
            course_num = course_id.split(" ")[1] if " " in course_id else ""
            level_info = ""
            if course_num:
                try:
                    level = int(course_num[0])
                    if level <= 4:
                        level_info = " (Undergraduate)"
                    else:
                        level_info = " (Graduate)"
                except:
                    pass
            
            # Add matching skills info
            matching = ", ".join(course.get("Matching Skills", []))
            skills_info = f" - Matches: {matching}" if matching else ""
            
            # Extract major
            if " " in course_id:
                prefix = course_id.split(" ")[0]
                major = prefix_to_major.get(prefix, "")
                major_info = f" [{major}]" if major else ""
            else:
                major_info = ""
            
            output += f"- **{course_id}**: {course['Course Name']}{level_info}{major_info} _{course['Match Type']}_ (Score: {course['Score']:.2f}){skills_info}\n"
        output += "\n"
    
    # Top MOOC courses
    if mooc_results:
        output += "#### Online Courses (MOOCs):\n\n"
        top_mooc = sorted(mooc_results, key=lambda x: -x["Score"])[:5]
        for course in top_mooc:
            course_name = course["Name"]
            added_mooc_courses.add(course_name)
            
            # Add matching skills info
            matching = ", ".join(course.get("Matching Skills", []))
            skills_info = f" - Matches: {matching}" if matching else ""
            
            output += f"- **{course_name}**: [Course Link]({course['Link']}) _{course['Match Type']}_ (Score: {course['Score']:.2f}){skills_info}\n"
        output += "\n"
    
    # Add recommendations by skill - but only for top weighted skills
    for skill_item in weighted_skills[:min(len(weighted_skills), 6)]:
        skill = skill_item["skill"]
        gt_for_skill = skill_to_courses[skill]["gt"]
        mooc_for_skill = skill_to_courses[skill]["mooc"]
        
        if gt_for_skill or mooc_for_skill:
            output += f"### 🔍 Courses for {skill.upper()}\n\n"
            
            # Add Georgia Tech courses for this skill
            if gt_for_skill:
                output += "#### Georgia Tech Courses:\n\n"
                sorted_courses = sorted(gt_for_skill, key=lambda x: -x["Score"])
                count = 0
                for course in sorted_courses:
                    course_id = course["Course ID"]
                    if course_id not in added_gt_courses and count < 3:
                        # Extract major and level
                        if " " in course_id:
                            prefix = course_id.split(" ")[0]
                            course_num = course_id.split(" ")[1]
                            major = prefix_to_major.get(prefix, "")
                            major_info = f" [{major}]" if major else ""
                            
                            level_info = ""
                            try:
                                level = int(course_num[0])
                                if level <= 4:
                                    level_info = " (Undergraduate)"
                                else:
                                    level_info = " (Graduate)"
                            except:
                                pass
                        else:
                            major_info = ""
                            level_info = ""
                        
                        output += f"- **{course_id}**: {course['Course Name']}{level_info}{major_info} _{course['Match Type']}_ (Score: {course['Score']:.2f})\n"
                        added_gt_courses.add(course_id)
                        count += 1
                output += "\n"
            
            # Add MOOC courses for this skill
            if mooc_for_skill:
                output += "#### Online Courses (MOOCs):\n\n"
                sorted_courses = sorted(mooc_for_skill, key=lambda x: -x["Score"])
                count = 0
                for course in sorted_courses:
                    course_name = course["Name"]
                    if course_name not in added_mooc_courses and count < 3:
                        output += f"- **{course_name}**: [Course Link]({course['Link']}) _{course['Match Type']}_ (Score: {course['Score']:.2f})\n"
                        added_mooc_courses.add(course_name)
                        count += 1
                output += "\n"
    
    if not gt_results and not mooc_results:
        output += "No matching courses found. Try modifying your job description with more technical details."
    
    return output

# Original recommendation function - updated to use the new implementation
def find_recommended_courses(job_title, job_description, skills=None):
    """Find courses that match the given job title, description, and skills"""
    # This function now serves as a wrapper for the new implementation
    # It maintains compatibility with the old interface
    return implement_course_recommendations(job_title, job_description, skills)
    
# Main UI
st.title("Job-to-Course Recommendation System")
st.write("This system analyzes job descriptions to recommend relevant courses from Georgia Tech and MOOCs.")

tab1, tab2, tab3, tab4 = st.tabs(["Get Recommendations", "Settings", "Vector Database", "Job-Major Mapping"])

with tab1:
    st.write("Enter a job title and description to get recommended courses.")
    job_title = st.text_input("Enter Job Title", "Data Scientist")
    job_description = st.text_area("Enter Job Description", "Looking for a data scientist with Python skills, experience in machine learning, and the ability to work with large datasets. Knowledge of data visualization and statistical analysis is required. Experience with deep learning frameworks like TensorFlow or PyTorch is a plus. The ideal candidate should be comfortable with cloud computing platforms and have experience with SQL databases. Knowledge of data engineering principles and ETL pipelines is beneficial.")
    
    # Add option for user to explicitly specify skills
    st.write("Optional: Specify additional skills (comma-separated)")
    user_skills = st.text_input("Additional Skills", "")
    
    # Job seniority level selection
    seniority_level = st.radio(
        "Seniority Level:",
        ["Entry-Level", "Mid-Level", "Senior"],
        horizontal=True,
        help="Select the seniority level of the position to get more appropriate course recommendations"
    )
    
    # Show relevant majors based on job title (informational)
    if job_title:
        relevant_majors = get_relevant_majors(job_title)
        major_str = ", ".join(relevant_majors)
        st.info(f"Relevant academic areas for {job_title}: {major_str}")
    
    if st.button("🔍 Find Recommended Courses"):
        if "datasets" not in st.session_state:
            st.error("Please load datasets in the Settings tab first!")
        else:
            with st.spinner("Finding relevant courses..."):
                # Use the new recommendation function that filters by major
                recommendations = implement_course_recommendations(job_title, job_description, user_skills, seniority_level)
                st.markdown(recommendations)
                
                # Add an option to download recommendations as markdown
                st.download_button(
                    label="Download Recommendations",
                    data=recommendations,
                    file_name=f"{job_title.replace(' ', '_')}_course_recommendations.md",
                    mime="text/markdown",
                )

with tab2:
    st.subheader("Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Dataset Paths")
        jobskills_path = st.text_input("JobSkills CSV Path", "~/desktop/6365 P/jobskills.csv")
        gt_courses_path = st.text_input("Georgia Tech Courses CSV Path", "~/desktop/6365 P/gatech_courses.csv")
        moocs_path = st.text_input("MOOCs CSV Path", "~/desktop/6365 P/moocs.csv")
    
    with col2:
        st.write("LLM API Settings")
        api_type = st.selectbox(
            "LLM API Type", 
            ["ollama", "together", "deepseek", "gemini"],
            help="Select which API to use for skill extraction"
        )
        st.session_state.api_type = api_type
        
        if api_type == "ollama":
            st.session_state.llm_api_url = st.text_input("Ollama API URL", "http://localhost:11434/api/generate")
            st.session_state.llm_model_name = st.text_input("Ollama Model Name", "llama3.2")
        elif api_type in ["together", "deepseek", "gemini"]:
            api_key = st.text_input(f"{api_type.capitalize()} API Key", type="password")
            st.session_state.api_key = api_key
            model_options = {
                "together": ["togethercomputer/llama-2-7b-chat", "togethercomputer/llama-2-70b-chat", "mistralai/Mistral-7B-Instruct-v0.1"],
                "deepseek": ["deepseek-ai/deepseek-llm-7b-chat", "deepseek-ai/deepseek-coder-6.7b-instruct"],
                "gemini": ["models/gemini-1.5-pro-latest",
    "models/gemini-1.5-pro-002",
    "models/gemini-1.5-flash-latest",
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.0-flash"]
            }
            st.session_state.llm_model_name = st.selectbox(
                f"{api_type.capitalize()} Model", 
                model_options.get(api_type, ["default_model"])
            )
    
    if st.button("Load Datasets"):
        with st.spinner("Loading datasets..."):
            st.session_state.datasets = load_datasets(jobskills_path, gt_courses_path, moocs_path)
            st.success("Datasets loaded successfully!")
    
    # Test LLM API
    if st.button("Test LLM API Connection"):
        test_description = "Looking for a Python developer with machine learning experience."
        with st.spinner("Testing API connection..."):
            skills = extract_skills("Developer", test_description, api_type)
            if skills:
                st.success(f"API connection successful! Extracted skills: {', '.join(skills)}")
            else:
                st.error("API connection failed. Check your settings and try again.")

with tab3:
    st.subheader("Vector Database Management")
    st.write("Initialize or refresh the vector database with your course data for semantic search.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Initialize Vector Database"):
            if "datasets" not in st.session_state:
                st.error("Please load datasets first!")
            else:
                with st.spinner("Initializing vector database... This may take a few minutes for large datasets."):
                    embedding_model = load_embedding_model()
                    success = initialize_vector_database(st.session_state.datasets, embedding_model)
                    if success:
                        st.success("Vector database initialized successfully!")
    
    with col2:
        if st.button("Refresh Vector Database"):
            if "datasets" not in st.session_state:
                st.error("Please load datasets first!")
            else:
                # Confirm refresh dialog
                refresh_confirm = st.warning("⚠This will delete and rebuild all vector database collections. Continue?")
                confirm_col1, confirm_col2 = st.columns(2)
                
                with confirm_col1:
                    if st.button("Yes, Refresh Data"):
                        with st.spinner("Refreshing vector database... This may take a few minutes."):
                            embedding_model = load_embedding_model()
                            success = refresh_vector_database(st.session_state.datasets, embedding_model)
                            if success:
                                st.success("Vector database refreshed successfully!")
                
                with confirm_col2:
                    if st.button("Cancel"):
                        st.info("Refresh canceled.")
    
    # Add information about when to refresh
    st.info("**When to refresh?** Refresh your vector database when you have updated your course data or if you notice that search results aren't matching correctly.")
    
    # Add selective refresh option
    st.subheader("Selective Refresh")
    refresh_options = st.multiselect("Select collections to refresh:", ["gt_courses", "moocs"], 
                                    help="Choose which collections to refresh instead of refreshing everything")
    
    if st.button("Refresh Selected Collections"):
        if "datasets" not in st.session_state:
            st.error("Please load datasets first!")
        elif not refresh_options:
            st.warning("Please select at least one collection to refresh.")
        else:
            # Create a subset of datasets with only the selected collections
            selected_datasets = {k: st.session_state.datasets[k] for k in refresh_options if k in st.session_state.datasets}
            
            with st.spinner(f"Refreshing selected collections: {', '.join(refresh_options)}"):
                embedding_model = load_embedding_model()
                success = refresh_vector_database(selected_datasets, embedding_model)
                if success:
                    st.success(f"Selected collections refreshed successfully: {', '.join(refresh_options)}")
with tab4:
    st.subheader("Job-to-Major Mapping")
    st.write("Customize which academic majors are relevant for different job titles.")
    
    # Show current mappings
    st.write("### Current Job-Major Mappings")
    
    # Allow user to select a job to edit
    job_options = list(job_to_major.keys())
    selected_job = st.selectbox("Select Job Title to Edit", job_options)
    
    if selected_job:
        # Show current majors for this job
        current_majors = job_to_major[selected_job]
        st.write(f"Current majors for {selected_job}:", ", ".join(current_majors))
        
        # Let user edit majors for this job
        all_majors = sorted(set(major for majors in job_to_major.values() for major in majors))
        
        selected_majors = st.multiselect(
            "Select Relevant Majors", 
            options=all_majors,
            default=current_majors
        )
        
        if st.button(f"Update Majors for {selected_job}"):
            # Update the mapping
            job_to_major[selected_job] = selected_majors
            st.success(f"Updated majors for {selected_job}")
    
    # Add new job title
    st.write("### Add New Job Title")
    new_job_title = st.text_input("New Job Title")
    
    if new_job_title:
        # Get all possible majors to select from
        all_majors = sorted(set(major for majors in job_to_major.values() for major in majors))
        
        new_job_majors = st.multiselect(
            "Select Relevant Majors for New Job", 
            options=all_majors
        )
        
        if st.button("Add New Job-Major Mapping"):
            if new_job_title and new_job_majors:
                job_to_major[new_job_title] = new_job_majors
                st.success(f"Added new job mapping for {new_job_title}")
            else:
                st.warning("Please provide both job title and majors")

# Add footer
st.markdown("---")
st.markdown("💡 **Tip:** For best results, use detailed job descriptions that mention specific technical skills.")