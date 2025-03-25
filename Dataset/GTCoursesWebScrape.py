from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Base URL for Georgia Tech Course Catalog
BASE_URL = "https://catalog.gatech.edu/coursesaz/"

# Open the page
driver.get(BASE_URL)
time.sleep(3)  # Wait for JavaScript to load

# Extract all course subject links
subjects = driver.find_elements(By.CSS_SELECTOR, "a.sc_sctn")
subject_links = [sub.get_attribute("href") for sub in subjects]

course_data = []

# Visit each subject page
for link in subject_links:
    driver.get(link)
    time.sleep(2)

    # Extract all course blocks
    courses = driver.find_elements(By.CSS_SELECTOR, "div.courseblock")
    
    for course in courses:
        try:
            course_id = course.find_element(By.CSS_SELECTOR, "p.courseblocktitle").text.strip()
            course_desc = course.find_element(By.CSS_SELECTOR, "p.courseblockdesc").text.strip()
            keywords = ", ".join(set(course_desc.split()[:10]))  # First 10 unique words as keywords
            course_data.append([course_id, course_desc, keywords])
        except:
            continue

# **Fixed Line Here**
df = pd.DataFrame(course_data, columns=["Course ID", "Description", "Keywords"])
df.to_csv("georgia_tech_courses.csv", index=False)  # Ensure this line is correct

print("CSV file 'georgia_tech_courses.csv' has been saved.")

# Close browser
driver.quit()
