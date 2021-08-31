import boto3
import os
import numpy as np
from collections import defaultdict

from lambda_decorators import cors_headers

import pandas as pd

from Person import *
from Form import *
from function import *

import json
import requests
import base64

from datetime import datetime, timezone
from pathlib import Path

from collections import defaultdict
from types import SimpleNamespace

from decouple import config

headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': True,
      'Content-Type':'application/json'
    }

try: # Fetch keys from .env file
    TF_ACCESS_KEY = config("TF_ACCESS_KEY")
    TF_BASE_URL = config("TF_BASE_URL")
except: # Fetch keys from GitHub environmental variables
    TF_ACCESS_KEY = os.getenv('TF_ACCESS_KEY')
    TF_BASE_URL = os.getenv("TF_BASE_URL")

auth = {'Authorization': 'Bearer '+ TF_ACCESS_KEY}

general_prefix = "/"
api_prefix = ""

MIN_SCORE = 1
MAX_SCORE = 10
CRON_MINS = 10

@cors_headers
def hello(event, context):
	return {
		'statusCode': 200,
        'headers': headers,
		'body': json.dumps("Hello world")
	}

@cors_headers
def extract_form_data(event, context):
    form_id = json.loads(event)
    form_id = form_id['form_id']
    
    responses = requests.get(TF_BASE_URL+"/forms/"+form_id+"/responses", headers=auth)
    form = requests.get(TF_BASE_URL+"/forms/"+form_id, headers=auth)
    
    resp = json.loads(responses.content)
    frm = json.loads(form.content)
    
    result = {
        "form_data":frm,
        "response_data":resp
    }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }

@cors_headers
def construct_df_from_form_data(event, context):
    data = event['body']
    data = json.loads(data)
    
    frm = data['form_data']
    resp = data['response_data']
    
    form = Form(frm['title'])
    
    cols = []
    rows = []

    opinion_fields = [field for field in frm['fields'] if field['type'] == 'opinion_scale']    
    total_score = sum((field['properties']['steps']-1) if field['properties']['start_at_one'] else field['properties']['steps'] for field in opinion_fields)
    
    for col in frm['fields']:
        if col['type'] == "email":
            cols.append("email")
        else:
            if col['type'] != "statement":
                cols.append(col['title'])
                
    for item in resp['items']:
        row = []

        for answer in item['answers']:
            tpe = answer['type']
            row.append(answer[tpe])

        rows.append(row)
    
    df = pd.DataFrame(rows, columns=cols)
    json_df = df.to_dict(orient="dict")
    
    dd = defaultdict(list)
    calculated_tuple = tuple(item['calculated'] for item in resp['items'])
        
    for d in calculated_tuple:
        for key, value in d.items():
            dd[key].append(value)
    
    response = {
        'dataframe':json_df,
        'calculated':dd,
        'total_scores':total_score,
        'form':json.dumps(form.__dict__)
    }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response)
    }

# @cors_headers
# def list_sheet_files(event, context):
#   SCOPES = ["https://www.googleapis.com/auth/drive"]
#   creds = authenticate(SCOPES)

#   service = build('drive', 'v3', credentials=creds)

#   results = service.files().list(
#       pageSize=10,
#       q="mimeType='application/vnd.google-apps.spreadsheet'",).execute()  
#   items = results.get('files', [])

#   if not items:
#       print('No files found.')
#   else:
#       print('Files:')
#       for item in items:
#           print(u'{0} ({1})'.format(item['name'], item['id']))

#   return {
#     'statusCode': 200,
#     'headers': headers,
#     'body': json.dumps(items)
#   }

@cors_headers
def generate_scores(event, context):  
    print("Starting score generation")

    data = event['body']
    data = json.loads(data)

    #########################################################
    # Construct basic dataset                               #
    #########################################################  

    df = pd.DataFrame.from_dict(data['dataframe'])

    #########################################################
    # Create scores                                         #
    #########################################################  
        
    df['raw_score'] = data['calculated']['score']
    df['score'] = (df['raw_score']/data['total_scores'])*MAX_SCORE
    df['score'] = np.round(df['score']).astype("int")
    
    df = df[['email','score']]
    
    #########################################################
    # DF to JSON                                            #
    #########################################################    
    json_df = df.to_dict(orient="records")

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(json_df)
    }

@cors_headers
def generate_pdfs(event, context):   
    data = event['body']
    data = json.loads(data)
    
    personList = []

    for person in data[:1]:
        personList.append(
            Person(email=person['email'],
                   score=person['score'])
        )   
    
    resultsList = []
    
    for person in personList: 
        result = {}
        
        in_filename = "quickscan"
        out_filename = "Rapport Quickscan.pdf"
        
        filepath = general_prefix+"tmp/"+out_filename
        
        print(person.score)
        generate_pdf_from_template(person, filepath, api_prefix, in_filename, MIN_SCORE, MAX_SCORE)
        print("Saved report at "+filepath)

        with open(filepath, "rb") as f:
            b = base64.b64encode(f.read()).decode("utf-8")
            
        result['person'] = json.dumps(person.__dict__)
        result['report'] = b
        result['report_title'] = out_filename
        resultsList.append(result)
    
    pdf_headers = headers.copy()
    pdf_headers['Content-Type'] = 'application/pdf'
        
    return {
        'statusCode': 200,
        'headers': pdf_headers,
        'body': json.dumps(resultsList),
        "isBase64Encoded": True
    }

@cors_headers
def send_emails(event, context):
    data = event['body']
    data = json.loads(data)
            
    for i,entity in enumerate(data):    
#         person = Person(entity['person']['email'])
        person = json.loads(entity['person'], object_hook=lambda d: SimpleNamespace(**d))
        print(person)
        
        filepath = general_prefix+"tmp/"+entity['report_title']
        
        sender = "Neuro Habits <info@neurohabits.nl>"
        recipient = person.email
        aws_region = "eu-central-1"
        subject = "Uw Quickscan Stressrapport"
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(entity['report']))
            
        send_mail_with_attach_ses(sender, recipient, aws_region, subject, filepath, person)

        mails_sent = i+1

    result = {
        'mails_sent':mails_sent
    }
        
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }

@cors_headers
def selfscan_cron(event, context):
    form_ids = ['vaXpvkUJ']
    mails_sent = []
    
    for form_id in form_ids:
        request = json.dumps({'form_id':form_id})

        #########################################################
        # Only fetch data younger than x minutes                #
        #########################################################  
        form_data = extract_form_data(request,None)
        form_data = json.loads(form_data['body'])
        response_data = form_data['response_data']

        for i,response in enumerate(response_data['items'][:]):
            submitted_time = datetime.fromisoformat(response['submitted_at'].replace('Z', '+00:00'))
            curr_time = datetime.now(timezone.utc)

            minutes_diff = (curr_time-submitted_time).total_seconds() / 60.0
            if minutes_diff <= CRON_MINS:
                print(minutes_diff)
            else:
                response_data['items'].remove(response)
        
        if len(response_data['items']) == 0:
            mails_sent.append(0)
            break
            
        form_data['response_data'] = response_data
        form_data = {
            'body':json.dumps(form_data)
        }
        
        df = construct_df_from_form_data(form_data,None)
        
        scores = generate_scores(df,None)

        pdfs = generate_pdfs(scores,None)

        mails = send_emails(pdfs, None)
        mails = mails['body']
        mails = json.loads(mails)
        
        mails_sent.append(mails['mails_sent'])

    result = {
        'forms':form_ids,
        'mails_sent':mails_sent
    }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }