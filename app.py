import boto3
import os
import numpy as np
from collections import defaultdict

from lambda_decorators import cors_headers

import pandas as pd

import sys
sys.path.append('../functions')

import json
import requests
import base64

from datetime import datetime, timezone
from pathlib import Path

from collections import Counter

from types import SimpleNamespace

from decouple import config

from classes.Form import *
from classes.Person import *
from classes.Vitality import *
from classes.Education import *

# %%

headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': True,
      'Content-Type':'application/json'
    }

TF_ACCESS_KEY = config("TF_ACCESS_KEY")
TF_BASE_URL = config("TF_BASE_URL")

auth = {'Authorization': 'Bearer '+ TF_ACCESS_KEY}

# general_prefix = "" # Local
general_prefix = "/" # Production
api_prefix = ".."

MIN_SCORE = 1
MAX_SCORE = 10
CRON_MINS = 10

education_info = {
    "class_name":"Education",
    "class_attrs":{
        "score_offset":[261, 261, 261],
        "offset_vertical":[556, 402, 258],
        "offset_horizontal":[75, 75, 75],
        "variables_in_order":['autonomie', 'relatie', 'competentie'],
        "api_prefix":api_prefix,
        "general_prefix":general_prefix,
        "report_folder":"onderwijs_quickscan",
        "out_filename":"Rapport Quickscan.pdf",
        "template_link": "https://preview.mailerlite.com/o3u9q3"
    }
}

vitality_info = {
    "class_name":"Vitality",
    "class_attrs":{
        "score_offset":[261],
        "offset_vertical":[310],
        "offset_horizontal":[127],
        "variables_in_order":['result'],
        "api_prefix":api_prefix,
        "general_prefix":general_prefix,
        "report_folder":"stress_quickscan",
        "out_filename":"Rapport Quickscan.pdf",
        "template_link": "https://preview.mailerlite.com/i6e0h6"
    }
}

init_info = [
    {
        "type": 'Education',
        "class_info": education_info,
        "stage": [
            {
                "stage": "dev",
                "form_id": "v3q6i6Lm"
            }
        ]
    },
    {
        "type": 'Vitality',
        "class_info": vitality_info,
        "stage": [
            {
                "stage": "dev",
                "form_id": "vaXpvkUJ"
            },
            {
                "stage": "prod",
                "form_id": "vOPz3zmu"
            }
        ]
    }
]

# %%

@cors_headers
def hello(event, context):
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps("Hello world")
    }

# %%

@cors_headers
def extract_form_data(event, context):
    data = json.loads(event)
    form_id = data['form_id']

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

# %%

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
    variables_list = np.array([item['variables'] for item in resp['items']])

    score_list = []
    for item in variables_list:
        temp_dict = {}
        for i in item:
            print(i)
            temp_dict[i['key']] = i['number']

        score_list.append(temp_dict)

    dd = create_dict_with_lists(score_list)
    print(dd)

    # New code
    frm_vars = frm['variables']
    score_dict = frm_vars.copy()

    for logic in frm['logic']:
        max_val = 0

        target_dict = {}
        for actions in logic['actions']:
            action, target, source = actions.values()

            tgt_var = target['target']['value']
            tgt_val = target['value']['value']

            if action == 'add' and tgt_val > frm_vars[tgt_var]:
                target_dict[tgt_var] = tgt_val

        score_dict = dict(Counter(score_dict) + Counter(target_dict))
    # End

    response = {
        'dataframe':json_df,
        'scores':dd,
        'max_scores':score_dict,
        'form':json.dumps(form.__dict__)
    }

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response)
    }

# %%

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

    df = pd.DataFrame()
    df['email'] = data['dataframe']['email'].values()

    #########################################################
    # Create scores                                         #
    #########################################################
    for key, value in data['max_scores'].items():
        df[key] = [(x / data['max_scores'][key])*MAX_SCORE for x in data['scores'][key]]

    #     df['raw_scores'] = data['scores']
    #     df['final_scores'] = (df['raw_score']/data['total_scores'])*MAX_SCORE
    #     df['final_scores'] = np.round(df['final_scores']).astype("int")

    #     df = df[['email','final_scores']]

    #########################################################
    # DF to dict                                            #
    #########################################################
    json_df = df.to_dict(orient="records")

    #########################################################
    # Create final dict                                     #
    #########################################################
    response = {
        'dataframe':json_df,
        'variables':list(data['max_scores'].keys())
    }

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response)
    }

# %%

@cors_headers
def generate_pdfs(event, context):
    print("Generating PDFs")
    print("---")
    data = event['body']
    data = json.loads(data)

    df = data['dataframe']
    variables = data['variables']
    class_inf = data['class_info']

    class_attrs = class_inf['class_attrs']

    out_filename = class_attrs['out_filename']

    filepath = general_prefix+"tmp/"+out_filename

    if class_inf['class_name'] == 'Vitality':
        _class = Vitality(class_attrs)

    elif class_inf['class_name'] == 'Education':
        _class = Education(class_attrs)

    for key, val in class_attrs.items():
        setattr(_class,key,val)

    personList = []

    for person in df:
        _person = Person(
            email=person['email']
        )

        for var in variables:
            setattr(_person, var, person[var])

        personList.append(_person)

    resultsList = []

    for person in personList:
        result = {}

        _class.person = person
        _class.init_super()

        print(_class.__dict__)

        create_canvas = _class.create_canvas()
        create_canvas

        with open(filepath, "rb") as f:
            print("Encoding PDF")
            b = base64.b64encode(f.read()).decode("utf-8")

        result['report'] = b
        result['person'] = json.dumps(person.__dict__)
        result['class_info'] = json.dumps(class_inf)
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

# %%

@cors_headers
def send_emails(event, context):
    print("Sending emails")
    print("---")
    data = event['body']
    data = json.loads(data)

    for i,entity in enumerate(data):
        person = json.loads(entity['person'], object_hook=lambda d: SimpleNamespace(**d))
        class_info =  json.loads(entity['class_info'])
        print(class_info)

        filepath = general_prefix+"tmp/"+entity['report_title']

        sender = "Neuro Habits <info@neurohabits.nl>"
        recipient = person.email
        aws_region = "eu-central-1"
        subject = "Uw Quickscan Rapport"

        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(entity['report']))

        print(class_info['class_attrs'])
        send_mail_with_attach_ses(sender,
                                  recipient,
                                  aws_region,
                                  subject,
                                  filepath,
                                  person,
                                  class_info['class_attrs']['template_link'])

        mails_sent = i+1

    result = {
        'mails_sent':mails_sent
    }

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }

# %%

@cors_headers
def selfscan_cron(event, context):
    form_ids = []

    form_ids.append({
        'form_id':fetch_form_id('Education', 'dev', init_info),
        'class_info':education_info
    })
    form_ids.append({
        'form_id':fetch_form_id('Vitality', 'dev', init_info),
        'class_info':vitality_info
    })

    mails_sent = []

    for form_id in form_ids:
        request = json.dumps({'form_id':form_id['form_id']})

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

        # Insert class info
        z = scores['body']
        z = json.loads(z)

        z['class_info'] = form_id['class_info']
        scores['body'] = json.dumps(z)
        # End

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
