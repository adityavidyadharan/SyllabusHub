from flask import Blueprint, request, jsonify
import os
from functools import lru_cache
from flask_cors import CORS
# Import all the necessary functions from your rec.py
from backend.rec import (load_embedding_model, setup_vector_db, load_datasets,
                        get_relevant_majors)

rec = Blueprint('rec', __name__)
CORS(rec, resources={r"/*": {"origins": "*"}})

# Define paths for your datasets
''' DATASETS_PATH = {
    "jobskills": os.path.expanduser("~/desktop/6365 P/jobskills.csv"),
    "gt_courses": os.path.expanduser("~/desktop/6365 P/gatech_courses.csv"),
    "moocs": os.path.expanduser("~/desktop/6365 P/moocs.csv")
}'''

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create absolute paths by joining with the base directory
DATASETS_PATH = {
    "jobskills": os.path.join(BASE_DIR,"backend", "Dataset", "jobskills.csv"),
    "gt_courses": os.path.join(BASE_DIR, "backend", "Dataset", "gatech_courses.csv"),
    "moocs": os.path.join(BASE_DIR,"backend", "Dataset", "moocs.csv")
}
print(DATASETS_PATH['gt_courses'])


# Set up a global configuration that will substitute for st.session_state
# Since Flask doesn't have session state like Streamlit
API_CONFIG = {
    "api_type": "gemini",
    "llm_model_name": "models/gemini-2.0-flash-lite",
    "api_key": os.environ.get("GEMINI_API_KEY", "")  # Get from environment variable
}

# Cache datasets and models
@lru_cache(maxsize=1)
def get_cached_data():
    print("Loading cached datasets...")
    datasets = load_datasets(
        DATASETS_PATH["jobskills"],
        DATASETS_PATH["gt_courses"],
        DATASETS_PATH["moocs"]
    )
    print(DATASETS_PATH['gt_courses'])

    embedding_model = load_embedding_model()
    return datasets, embedding_model


# Import the fixed implementation
#from api_implement_course_recommendations import api_implement_course_recommendations

# This is the complete version of the api_implement_course_recommendations function
# It ensures we get the same output as the Streamlit version including MOOCs and skill-wise recommendations

def api_implement_course_recommendations(job_title, job_description, user_skills=None, seniority_level="Mid-Level"):
    """API-specific version that doesn't rely on st.session_state"""
    from backend.rec import (enhanced_skill_extraction, weight_skills, get_relevant_majors,
                            is_relevant_major_course, improved_direct_search, 
                            improved_semantic_search, combine_results, advanced_filtering,
                            normalize_skills, prefix_to_major)
    
    # Map seniority level to internal representation
    job_level_mapping = {
        "Entry-Level": "entry",
        "Mid-Level": "mid",
        "Senior": "senior"
    }
    job_level =  "mid"
    
    # Get datasets and embedding model
    datasets, embedding_model = get_cached_data()
    
    # 1. Get relevant majors for this job
    relevant_majors = get_relevant_majors(job_title)
    print(f"Relevant Majors for {job_title}: {', '.join(relevant_majors)}")
    
    # 2. Extract and normalize skills - pass the API config
    # Create a simple wrapper for extract_skills_gemini
    def api_extract_skills(job_title, job_description, api_type="gemini"):
        try:
            import google.generativeai as genai
            
            # Configure with API key from our config
            genai.configure(api_key=API_CONFIG["api_key"])
            
            # Create a model instance
            model = genai.GenerativeModel(
                model_name=API_CONFIG["llm_model_name"],
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
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract just the skills list
            skills_text = ""
            if "Skills:" in response_text:
                skills_section = response_text.split("Skills:")[1].split("Relevant Majors:")[0].strip()
                skills_text = skills_section
            
            skills_list = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
            return skills_list
            
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            # Fallback to hardcoded skills for common job titles
            if "data scientist" in job_title.lower():
                return ["python", "machine learning", "statistics", "data analysis", "sql"]
            elif "software" in job_title.lower() and "engineer" in job_title.lower():
                return ["software engineering", "python", "algorithms", "data structures", "system design"]
            elif "network" in job_title.lower():
                return ["network monitoring", "software engineering", "algorithms", "python", "scalable systems"]
            else:
                # Try to extract skills using regex for basic keywords in the job description
                from backend.rec import fallback_skill_extraction
                return fallback_skill_extraction(job_description)
    
    # Modified enhanced_skill_extraction to use our API wrapper
    def api_enhanced_skill_extraction(job_title, job_description, user_skills=None):
        # Get skills from our API wrapper
        extracted_skills = api_extract_skills(job_title, job_description)
        
        # If we couldn't extract skills, try fallback
        if not extracted_skills:
            from backend.rec import fallback_skill_extraction
            extracted_skills = fallback_skill_extraction(job_description)
        
        # Include user-provided skills if any
        if user_skills:
            if isinstance(user_skills, str):
                user_skills = [s.strip() for s in user_skills.split(',')]
            
            # Add user skills to extracted skills, avoiding duplicates
            for skill in user_skills:
                if skill and skill.strip() and skill.strip().lower() not in [s.lower() for s in extracted_skills]:
                    extracted_skills.append(skill.strip())
        
        # Use original normalize_skills function from backend.rec
        normalized_skills = normalize_skills(extracted_skills)
        
        # Limit to reasonable number
        return normalized_skills[:10]
    
    # Continue with the implementation using our modified functions
    normalized_skills = api_enhanced_skill_extraction(job_title, job_description, user_skills)
    print(f"Identified Skills: {', '.join(normalized_skills)}")
    
    if not normalized_skills:
        return "No skills could be extracted from the job description. Please try again with a more detailed description."
    
    # 3. Weight skills by importance
    weighted_skills = weight_skills(normalized_skills, job_title, job_description)
    
    # 4. Filter Georgia Tech courses by relevant majors
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
        print(f"Filtered from {len(gt_df)} courses to {len(relevant_gt_df)} courses in relevant majors")
    else:
        relevant_datasets = datasets
        print("GT courses dataset not available, skipping major filtering")
    
    # 5. Perform improved searches on filtered dataset
    gt_direct = improved_direct_search(relevant_datasets, weighted_skills, "gt_courses")
    gt_semantic = improved_semantic_search(relevant_datasets, weighted_skills, job_title, "gt_courses", embedding_model)
    gt_combined = combine_results(gt_direct, gt_semantic, "Course ID")
    
    # 6. Apply advanced filtering
    gt_filtered = advanced_filtering(gt_combined, "gt_courses", weighted_skills, job_title)
    
    # Apply job level weighting based on UI selection
    gt_results = []
    for course in gt_filtered:
        if "Course Level" in course:
            # Adjust scores based on seniority level
            if job_level == "entry" and course["Course Level"] == "Graduate":
                course["Score"] *= 0.9  # Downweight graduate courses for entry level
            elif job_level == "senior" and course["Course Level"] == "Undergraduate":
                course["Score"] *= 0.9  # Downweight undergraduate courses for senior level
        gt_results.append(course)
    
    # 7. For MOOCs, we can't easily filter by major, so search all MOOCs
    mooc_direct = improved_direct_search(datasets, weighted_skills, "moocs")
    mooc_semantic = improved_semantic_search(datasets, weighted_skills, job_title, "moocs", embedding_model)
    mooc_combined = combine_results(mooc_direct, mooc_semantic, "Name")
    mooc_results = advanced_filtering(mooc_combined, "moocs", weighted_skills, job_title)
    
    # 8. Group courses by skills they match
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
    
    # 9. Format the output
    output = f"## Course Recommendations for {job_title}\n\n"
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

@rec.route('/getrec', methods=['POST'])
def get_recommendations():
    """Endpoint to get course recommendations"""
    data = request.json
    job_title = data.get('jobTitle', '')
    job_description = data.get('jobDescription', '')
    user_skills = data.get('userSkills', '')
    #seniority_level = data.get('seniorityLevel', 'Mid-Level')
    
    # Get API key from request if provided
    if 'apiKey' in data and data['apiKey']:
        API_CONFIG['api_key'] = data['apiKey']
    
    try:
        print(f"Processing request for job title: {job_title}")
        #print(f"Seniority level: {seniority_level}")
        print(f"API key length: {len(API_CONFIG['api_key'])}")
        
        # Use our API-specific implementation
        recommendations = api_implement_course_recommendations(
            job_title,
            job_description,
            user_skills
            #seniority_level
        )
        
        print(f"Generated recommendations of length: {len(recommendations)}")
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@rec.route('/relevant-majors', methods=['GET'])
def api_relevant_majors():
    job_title = request.args.get('jobTitle', '')
    relevant_majors = get_relevant_majors(job_title)
    return jsonify({"relevantMajors": relevant_majors})

# Add a new route for API configuration
@rec.route('/configure', methods=['POST'])
def configure_api():
    """Endpoint to update API configuration"""
    data = request.json
    
    # Update API configuration
    if 'apiKey' in data:
        API_CONFIG['api_key'] = data['apiKey']
    
    if 'apiType' in data:
        API_CONFIG['api_type'] = data['apiType']
    
    if 'modelName' in data:
        API_CONFIG['llm_model_name'] = data['modelName']
    
    return jsonify({"message": "Configuration updated successfully"})