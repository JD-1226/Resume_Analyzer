from django.shortcuts import render, redirect 
from django.core.files.storage import FileSystemStorage
import PyPDF2 
from .utils import extract_keywords 
import os 


# Create your views here.
def upload_resume(request):
    if request.method == 'POST' and request.FILES['resume']:
        resume = request.FILES['resume'] 
        fs = FileSystemStorage()
        filename = fs.save(resume.name, resume)
        file_path = fs.path(filename)


        #Extract text from pdf
        text = ""
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() or ""


        #Extract keywords
        skills = extract_keywords(text)

        #store skills in session
        request.session['skills'] = skills 
        return redirect('results')


    return render(request, 'upload.html')


def results(request):
    skills = request.session.get('skills', []) 
    job_links = []


    #Simple job link generation based on skills
    for skill in skills:
        job_links.append({
            "skill": skill.title(),
            "linkedin" : f"https://www.linkedin.com/jobs/search/?keywords={skill}+developer",
            "naukri" : f"https://www.naukri.com/{skill}-jobs",
            "google": f"https://www.google.com/search?q={skill}+jobs"
        })


    return render(request, 'results.html', {'job_links': job_links})