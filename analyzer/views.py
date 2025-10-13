from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import PyPDF2 
import os 


# Create your views here.
def upload_resume(request):
    text=''
    if request.method == 'POST' and request.FILES['resume']:
        resume = request.FILES['resume'] 
        fs = FileSystemStorage()
        filename = fs.save(resume.name, resume)
        file_path = fs.path(filename)


        #Extract text from pdf
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() or ""


    return render(request, 'upload.html', {'text': text})