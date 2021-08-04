import boto3
import os
import numpy as np

from lambda_decorators import cors_headers

import pandas as pd

from Person import *
from function import *

import json
import requests
import config
import base64

from datetime import datetime, timezone
from pathlib import Path

headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': True,
      'Content-Type':'application/json'
    }

auth = {'Authorization': 'Bearer '+ config.access_key}

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
    print(form_id)
    
    responses = requests.get(config.base_url+"/forms/"+form_id+"/responses", headers=auth)
    form = requests.get(config.base_url+"/forms/"+form_id, headers=auth)
    
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
    
    cols = []
    rows = []

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
    json_df = df.to_dict(orient="records")
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(json_df)
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
    MAX_SCORERANGE = 5
    MAX_SCORE = 10
    print("Starting score generation")

    data = event['body']
    data = json.loads(data)

    #########################################################
    # Construct basic dataset                               #
    #########################################################  

    df = pd.DataFrame(data)

    #########################################################
    # Create scores                                         #
    #########################################################  
    
    numeric_df = df.select_dtypes(include=[np.number])
    
    df['raw_score'] = numeric_df.sum(axis=1) / len(numeric_df.columns)
    df['score'] = (df['raw_score']/MAX_SCORERANGE)*MAX_SCORE
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

    for person in data:
        personList.append(
            Person(email=person['email'],
                   score=person['score'])
        )   
    
    resultsList = []
    
    for person in personList: 
        result = {}
        
        filepath = "/tmp/report.pdf"
        generate_pdf_from_template(person, filepath)

        with open(filepath, "rb") as f:
            b = base64.b64encode(f.read()).decode("utf-8")
            
        result['person'] = person.__dict__
        result['report'] = b
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
        person = Person(entity['person']['email'])
        
        filepath = "/tmp/report.pdf"
        
        sender = "sebastiaan@somnitas.com"
        aws_region = "eu-central-1"
        subject = "Uw Quickscan Stressrapport"
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(entity['report']))
            
        send_mail_with_attachment(person, sender, aws_region, subject, filepath)

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
    form_ids = ['vOPz3zmu']
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
            if minutes_diff > 10:
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