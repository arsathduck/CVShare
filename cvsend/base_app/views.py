import os
import glob
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from base_app import forms
from django.core.files.storage import default_storage

# Imports for sending mails
import smtplib
import time
import pandas
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def index(request):

    # below we have mentioned the variable form which will be used to display form
    form= forms.mail_datas
    if request.method =="POST":
        # Below used to get datas if the user post datas
        form = forms.mail_datas(request.POST, request.FILES)

        if form.is_valid():
            # create the folder if it doesn't exist.
            try:
                os.mkdir(os.path.join(settings.MEDIA_ROOT, folder))
            except:
                pass
            file = request.FILES['user_file']
            file_name = default_storage.save(file.name, file)
            file = request.FILES['resume_file']
            resume_name = default_storage.save(file.name, file)

            data = pandas.read_excel(f"media/{file_name}")
            dicted_data = data.to_dict()
            # Raising error if file not contain expected keyword
            try:
                MAIL_LENGTH = len(dicted_data["email"])
            except:
                return JsonResponse(
                    {'message': 'KeyError',
                     'explanation': 'Mail send failed as there is no cell found in 1st row contain key email in uploaded excel sheet.'},
                    status='400')

            print(f"Have fed with {MAIL_LENGTH} mail addresses")

            for n in range(0, MAIL_LENGTH):

                TO_EMAIL = dicted_data['email'][n]

                # Raising error if file not contain expected keyword
                try:
                    DESIGNATION = dicted_data['designation'][n]
                except:
                    return JsonResponse(
                        {'message': 'KeyError',
                         'explanation': 'Mail send failed as there is no cell found in 1st row contain key designation in uploaded excel sheet.'}, status='400')

                SUBJECT = form.cleaned_data['subject'].replace("<DESIG>", DESIGNATION)
                BODY = form.cleaned_data["message"].replace("<DESIG>", DESIGNATION)
                msg = MIMEMultipart()
                MY_MAIL = form.cleaned_data['email']
                PASSWORD = form.cleaned_data['token']
                msg['From'] = MY_MAIL
                msg['To'] = TO_EMAIL
                msg['Subject'] = SUBJECT
                msg.attach(MIMEText(BODY, 'plain'))
                pdfname = resume_name
                # open the file in bynary
                binary_pdf = open("media/" + pdfname, 'rb')
                payload = MIMEBase('application', 'octate-stream', Name=pdfname)
                # payload = MIMEBase('application', 'pdf', Name=pdfname)
                payload.set_payload((binary_pdf).read())
                # enconding the binary into base64
                encoders.encode_base64(payload)
                # add header with pdf name
                payload.add_header('Content-Decomposition', 'attachment', filename=pdfname)
                # Raising error if error while attaching file to mail
                try:
                    msg.attach(payload)
                except:
                    return JsonResponse(
                        {'message': 'Login Error', 'explanation': 'Failed to attach resume with mail, refresh page and try again.'},status='400')
                session = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                # Error raising for incorrect email/token fed
                try:
                    session.login(MY_MAIL, PASSWORD)
                except:
                    return JsonResponse({'message': 'Login Error', 'explanation': 'Kindly verify provided email id and token.'}, status='400')
                text = msg.as_string()

                session.sendmail(MY_MAIL, TO_EMAIL, text)
                time.sleep((15))

                print(f"Mail send success To {TO_EMAIL} applying for {DESIGNATION}.")

            try:
                files = glob.glob(os.path.join('media/*'))
                for f in files:
                    os.remove(f)
                    err_data=""
            except:
                err_data = {'error_msg_file_clean':'We found an error while vanishing datas. Try to do successful batch mail again to do clean. If not contact Admin'}

        # return for successful form submit
        return render(request, "result.html", {"err_data":err_data,
                                               "total_mail_send":MAIL_LENGTH})

    # render for first login to page
    return render(request, "index.html", {"form":form})

# By this page we get to know how to use this web
def docs(request):
    return render(request, "documentation.html")
