from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import PyPDF2, time, re, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import extract_keywords


# ========= PDF Upload ==========
def upload_resume(request):
    if request.method == 'POST' and request.FILES['resume']:
        resume = request.FILES['resume']
        fs = FileSystemStorage()
        filename = fs.save(resume.name, resume)
        file_path = fs.path(filename)

        # Extract text from PDF
        text = ""
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() or ""

        # Extract keywords
        skills = extract_keywords(text)
        request.session['skills'] = skills

        return redirect('results')

    return render(request, 'upload.html')


# ========= Optimized Selenium Setup ==========
def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.page_load_strategy = 'eager'  # Faster than normal
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(15)
    return driver


# ========= Scraping Functions ==========
def scrape_naukri(driver, skill, search_type):
    results = []
    try:
        url = f"https://www.naukri.com/{skill}-{'internship-' if 'intern' in search_type else ''}jobs-in-india"
        driver.get(url)
        time.sleep(2)
        job_cards = driver.find_elements(By.CSS_SELECTOR, ".jobTuple")[:15]
        for job in job_cards:
            try:
                title = job.find_element(By.CSS_SELECTOR, ".title").text
                company = job.find_element(By.CSS_SELECTOR, ".companyInfo .comp-name").text
                location = job.find_element(By.CSS_SELECTOR, ".locWdth").text
                link = job.find_element(By.CSS_SELECTOR, "a.title").get_attribute("href")
                results.append({
                    "source": "Naukri", "skill": skill,
                    "title": title, "company": company,
                    "location": location, "link": link, "posted": "N/A"
                })
            except:
                continue
    except Exception as e:
        print(f"[Naukri] {skill} → {e}")
    return results


def scrape_indeed(driver, skill, search_type):
    results = []
    try:
        url = f"https://in.indeed.com/jobs?q={skill}+{search_type}&l=India"
        driver.get(url)
        time.sleep(3)
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")[:15]
        for job in job_cards:
            try:
                title = job.find_element(By.CSS_SELECTOR, "h2.jobTitle").text
                company = job.find_element(By.CSS_SELECTOR, "span.companyName").text
                location = job.find_element(By.CSS_SELECTOR, "div.companyLocation").text
                link = job.find_element(By.CSS_SELECTOR, "h2.jobTitle a").get_attribute("href")
                posted = job.find_element(By.CSS_SELECTOR, "span.date").text if job.find_elements(By.CSS_SELECTOR, "span.date") else "N/A"
                results.append({
                    "source": "Indeed", "skill": skill,
                    "title": title, "company": company,
                    "location": location, "link": link, "posted": posted
                })
            except:
                continue
    except Exception as e:
        print(f"[Indeed] {skill} → {e}")
    return results


def scrape_google(driver, skill, search_type):
    results = []
    try:
        query = f"{skill}+{search_type}+jobs+in+India"
        driver.get(f"https://www.google.com/search?q={query}")
        time.sleep(2)
        search_results = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")[:10]
        for res in search_results:
            try:
                title = res.find_element(By.TAG_NAME, "h3").text
                link = res.get_attribute("href")
                results.append({
                    "source": "Google", "skill": skill,
                    "title": title, "company": "N/A",
                    "location": "N/A", "link": link, "posted": "N/A"
                })
            except:
                continue
    except Exception as e:
        print(f"[Google] {skill} → {e}")
    return results


# ========= Parallel Job Scraper ==========
def scrape_jobs_for_all(skills, search_type="jobs"):
    all_results = []
    scrapers = [scrape_naukri, scrape_indeed, scrape_google]

    # Run all skill scrapes in parallel threads
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for skill in skills:
            for scraper in scrapers:
                futures.append(executor.submit(run_scraper_thread, scraper, skill, search_type))

        for future in as_completed(futures):
            all_results.extend(future.result())

    return all_results


def run_scraper_thread(scraper_func, skill, search_type):
    driver = create_driver()
    results = scraper_func(driver, skill, search_type)
    driver.quit()
    return results


# ========= Django View ==========
def results(request):
    skills = request.session.get('skills', [])
    search_type = request.GET.get('type', 'jobs')
    all_jobs = scrape_jobs_for_all(skills, search_type)
    return render(request, 'results.html', {"all_jobs": all_jobs, "search_type": search_type})
