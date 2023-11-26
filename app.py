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

from config import *

from datetime import datetime, timezone
from pathlib import Path

from collections import Counter

from types import SimpleNamespace

from decouple import config

from classes.Form import *
from classes.Person import *
from classes.Vitality import *
from classes.Education import *
from classes.VitalityHLR import *
from classes.VitalityIchtus import *
from classes.VitalityUMCLong import *
from classes.VitalityUMCShort import *
from classes.WeManity import *

lambda_env = config("LAMBDA_ENV")
general_prefix = "/" if lambda_env == "True" else ""
# %%

# form_ids = [
#     {
#         'form_id': fetch_form_id('Education Quickscan', 'dev', init_info),
#         'class_info': json.load(open("report_templates/onderwijs_quickscan/config.json"))
#     },
#     {
#         'form_id': fetch_form_id('Vitality Ichtus', 'dev', init_info),
#         'class_info': json.load(open("report_templates/vitality_ichtus/config.json"))
#     },
#     {
#         'form_id': fetch_form_id('Vitality UMC Long', 'dev', init_info),
#         'class_info': json.load(open("report_templates/vitalityUMCLong/config.json"))
#     },
#     {
#         'form_id': fetch_form_id('Vitality UMC Short', 'dev', init_info),
#         'class_info': json.load(open("report_templates/vitalityUMCShort/config.json"))
#     },
#     {
#         'form_id': fetch_form_id('Vitality MCA', 'dev', init_info),
#         'class_info': json.load(open("report_templates/vitality_ichtus/config.json"))
#     },
#     {
#         'form_id': fetch_form_id('WeManity', 'dev', init_info),
#         'class_info': json.load(open("report_templates/wemanity/config.json"))
#     }
# ]


# Test just a single form before including it in the list
form_ids = [
    {
        'form_id': fetch_form_id('WeManity', 'dev', init_info),
        'class_info': json.load(open("report_templates/wemanity/config.json"))
    },
    {
        'form_id': fetch_form_id('WeManity EN', 'dev', init_info),
        'class_info': json.load(open("report_templates/wemanity/config_en.json"))
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
    form_info = data['form_info']

    params = {'page_size': 50}
    responses = requests.get(TF_BASE_URL + "/forms/" + form_info['form_id'] + "/responses", headers=auth, params=params)
    form = requests.get(TF_BASE_URL + "/forms/" + form_info['form_id'], headers=auth)

    resp = json.loads(responses.content)
    frm = json.loads(form.content)

    result = {
        "form_info": form_info,
        "form_data": frm,
        "response_data": resp
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
    frm_info = data['form_info']

    form = Form(frm['title'])

    cols = []
    col_ids = []
    rows = []

    opinion_fields = [field for field in frm['fields'] if field['type'] == 'opinion_scale']
    total_score = sum(
        (field['properties']['steps'] - 1) if field['properties']['start_at_one'] else field['properties']['steps'] for
        field in opinion_fields)

    for col in frm['fields']:
        if col['type'] != "statement":  # Since statements don't have certain properties like 'required'
            col_ids.append(col['id'])
            if col['type'] == "email":
                cols.append("email")
            else:
                cols.append(col['title'])

    print("Number of fields in survey:", str(len(frm['fields'])))
    print("Number of respondents in survey:", str(len(resp['items'])))

    print("Column IDs:")
    print(col_ids)

    print(f"Nr of columns in list: {len(col_ids)}")

    for item in resp['items']:
        row = []

        i = j = 0
        while j < len(col_ids):
            if i < (len(item['answers'])):
                answer = item['answers'][i]

                if answer['field']['id'] == col_ids[j]:
                    tpe = answer['type']
                    row.append(answer[tpe])
                    i += 1
                    j += 1
                else:
                    print("added")
                    row.append('no answer')
                    j += 1

            else:
                print("added")
                row.append('no answer')
                j += 1

        rows.append(row)

    print(rows)

    df = pd.DataFrame(rows, columns=cols)
    json_df = df.to_dict(orient="dict")

    dd = defaultdict(list)

    # variables_list = np.array([item['variables'] for item in resp['items']])

    url_list = []
    ## New part
    # If a question dictionary exists we want to calculate the scores based on this file
    if 'question_dict' in frm_info['class_info']['class_attrs']:
        print("Using new part")
        f = open("report_templates/" + frm_info['class_info']['class_attrs']['question_dict'], encoding="utf-8")
        question_dict = json.load(f)

        fields = []

        for field in frm['fields']:
            item = dict()

            item['id'] = field['id']
            item['title'] = field['title']
            item['type'] = field['type']

            if 'validations' in field:
                item['required'] = field['validations']['required']
            else:
                item['required'] = False

            fields.append(item)

        field_list = []
        for q in question_dict:
            category = q['category']

            for item in q['items']:
                item_dict = dict()
                item_dict['category'] = category

                for field in fields:
                    if field['title'] == item['question']:
                        item_dict['id'] = field['id']
                        item_dict['question'] = item['question']
                        item_dict['type'] = field['type']
                        item_dict['required'] = field['required']

                field_list.append(item_dict)

        print("Field list:")
        print(field_list)

        logic_list = []
        for logic in frm['logic']:
            for action in logic['actions']:
                try:
                    action_info = {'ref': action['condition']['vars'][1]['value'],
                                   'value': action['details']['value']['value']}

                    logic_list.append(action_info)
                except:
                    continue

        answer_list = []
        print("Number of respondents:", str(len(resp['items'])))
        for item in resp['items']:
            # Code block for when a URL is used in stead of email
            for v in item['variables']:
                if v['key'] == 'url':
                    url_list.append(v['number'])
            # end

            resp_list = []
            for answer in item['answers']:
                if answer['type'] == "number":
                    answer_info = {'field_id': answer['field']['id'], 'number': answer['number']}
                elif answer['type'] == "choice":
                    print(answer)

                    if 'ref' in answer['choice']:
                        answer_info = {'field_id': answer['field']['id'], 'ref': answer['choice']['ref']}
                    else:
                        print("There's no reference here. Skipping")

                resp_list.append(answer_info)

            answer_list.append(resp_list)

        # variables list must return [{'key':'Werkdruk', 'number':'_score'},{'key':'Emotionele belasting', 'number':'_score'}] for every respondent
        cats_score = []
        cats_unique = [q['category'] for q in question_dict]

        variables_list = []
        for i in range(len(resp['items'])):  # In the range of the respondents
            variables_list_resp = []

            for cat in cats_unique:
                cat_score = {"key": cat, "number": []}
                variables_list_resp.append(cat_score)

            for field in field_list:  # For every question
                try:
                    if field['type'] == 'multiple_choice' and field['required']:
                        answer = [answer for answer in answer_list[i] if answer['field_id'] == field['id']]
                        print(answer)
                        answer = answer[0]
                        logic = [logic for logic in logic_list if logic['ref'] == answer['ref']][0]['value']
                        for cat in variables_list_resp:
                            if field['category'] == cat['key']:
                                cat['number'].append(logic)
                                break

                    else:
                        for cat in variables_list_resp:
                            if field['category'] == cat['key'] and field['required']:
                                answer = [answer for answer in answer_list[i] if answer['field_id'] == field['id']][0]
                                cat['number'].append(answer['number'])
                                break
                except KeyError:
                    print("Found exception in following field:")
                    print(field)
                    sys.exit(1)

            for var in variables_list_resp:
                var['number'] = np.mean(var['number'])

            variables_list.append(variables_list_resp)

        print("Vars list")
        print(variables_list)

        score_list = []
        # For every item (respondent) in list of key: value pairs
        for item in variables_list:
            temp_dict = {}
            # For every key in the item
            for i in item:
                # Make a new key in a temporary dict where the value is equal to the total score by the respondent
                temp_dict[i['key']] = i['number']

            # Append temporary dictionary of respondent to main dict containing all respondents
            score_list.append(temp_dict)
    ## End new part

    # Use vars when declared in the typeform, use calculated score otherwise
    # if frm_info['class_info']['class_name'] != "Vitality HLR" and frm_info['class_info']['class_name'] != "Vitality Ichtus":
    else:
        variables_list = np.array([item['variables'] for item in resp['items']])
        print("Used vars")

        score_list = []
        # For every item (respondent) in list of key: value pairs
        for item in variables_list:
            temp_dict = {}
            # For every key in the item (e.g. 'anatomie')
            for i in item:
                temp_dict[i['key']] = i['number']
                # Make a new key in a temporary dict where the value is equal to the total score by the respondent

            # Append temporary dictionary of respondent to main dict containing all respondents
            score_list.append(temp_dict)

        # New code
        frm_vars = frm['variables']
        max_scores = frm_vars.copy()
        min_scores = frm_vars.copy()

        del min_scores['score']

        for logic in frm['logic']:
            max_val = 0

            target_dict = {}
            for actions in logic['actions']:
                action, target, source = actions.values()

                tgt_var = target['target']['value']
                tgt_val = target['value']['value']

                if action == 'add' and tgt_val > frm_vars[tgt_var]:
                    target_dict[tgt_var] = tgt_val

            max_scores = dict(Counter(max_scores) + Counter(target_dict))
        # End

    # Default code to transform into defaultdict
    dd = create_dict_with_lists(score_list)

    response = {
        'scores': dd,
        'urls': url_list,
        'dataframe': json_df,
        'form_info': frm_info,
        'form': json.dumps(form.__dict__)
    }

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response)
    }


# %%

@cors_headers
def generate_scores(event, context):
    print("Starting score generation")

    data = event['body']
    data = json.loads(data)
    #########################################################
    # Construct basic dataset                               #
    #########################################################

    df = pd.DataFrame()

    try:
        df['email'] = data['dataframe']['email'].values()
        df["url"] = None
    except KeyError:
        df['email'] = None
        df["url"] = data['urls']

    #########################################################
    # Create scores                                         #
    #########################################################
    for key, value in data['scores'].items():
        df[key] = data['scores'][key]

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
        'variables': list(data['scores'].keys()),
        'dataframe': json_df,
        'form_info': data['form_info']
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
    class_inf = data['form_info']['class_info']

    class_attrs = class_inf['class_attrs']

    out_filename = class_attrs['out_filename']

    filepath = general_prefix + "tmp/" + out_filename

    if class_inf['class_name'] == 'Vitality':
        _class = Vitality(class_attrs)

    elif class_inf['class_name'] == 'Education Quickscan':
        _class = Education(class_attrs)

    elif class_inf['class_name'] == 'Vitality HLR':
        _class = VitalityHLR(class_attrs)

    elif class_inf['class_name'] == 'Vitality Ichtus':
        _class = VitalityIchtus(class_attrs)

    elif class_inf['class_name'] == 'Vitality UMC Long':
        _class = VitalityUMCLong(class_attrs)

    elif class_inf['class_name'] == 'Vitality UMC Short':
        _class = VitalityUMCShort(class_attrs)

    elif class_inf['class_name'] == 'Vitality MCA':
        _class = VitalityIchtus(class_attrs)

    elif class_inf['class_name'] == 'WeManity':
        _class = WeManity(class_attrs)

    if fixScores != "None":
        # Create list of attributes
        attrs = [val for key, val in class_attrs.items() if key == "page_attrs"]
        # Create list of [[{'subject':'min/max score'}]]
        subjList = [[{"subject": k, "value": v[fixScores + '_score']} for k, v in attr.items()] for attr in attrs][0]
        print(subjList)

    for key, val in class_attrs.items():
        if fixScores != "None" and key == 'question_dict':
            print(val)

        setattr(_class, key, val)

    personList = []

    for person in df:
        _person = Person(
            email=person['email']
        )

        for var in variables:
            if fixScores != "None":
                setattr(_person, var, [subj["value"] for subj in subjList if subj["subject"] == var][0])
            else:
                setattr(_person, var, person[var])

        setattr(_person, "url", person["url"])

        personList.append(_person)

    resultsList = []

    for person in personList:
        print(f"Person dict: {person.__dict__}")
        result = {}

        _class.person = person
        _class.init_super()

        # print(_class.__dict__)

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
def send_reports(event, context):
    print("Sending reports")
    print("---")
    data = event['body']
    data = json.loads(data)

    for i, entity in enumerate(data):
        person = json.loads(entity['person'], object_hook=lambda d: SimpleNamespace(**d))
        class_info = json.loads(entity['class_info'])

        filepath = general_prefix + "tmp/" + entity['report_title']

        person.email = str(person.email)
        if person.email != 'nan':
            print("Using email")
            sender = "Neuro Habits <noreply@neurohabits.nl>"
            recipient = person.email
            aws_region = "eu-central-1"
            subject = "Jouw PSA rapport"

            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(entity['report']))

            if SEND_MAIL == "True":
                send_mail_with_attach_ses(sender,
                                          recipient,
                                          aws_region,
                                          subject,
                                          filepath,
                                          person,
                                          class_info['class_attrs']['template_link'])

        elif person.url != None:
            print("Using URL, uploading file to S3")
            print(f"Personal document number: {person.url}")

            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(entity['report']))

            upload_file_to_s3(filepath, "nh-psa-api", str(person.url) + "/" + entity['report_title'])

        else:
            print("No URL or email found")

        reports_sent = i + 1

    result = {
        'reports_sent': reports_sent
    }

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }


# %%

@cors_headers
def selfscan_cron(event, context):
    try:
        emails = event['emails']
    except:
        print("Emails not provided")

    reports_sent = []

    print(len(form_ids))
    for form_id in form_ids:
        print("Now using")
        print(form_id['form_id'])
        request = json.dumps({'form_info': form_id})

        #########################################################
        # Only fetch data younger than x minutes                #
        #########################################################
        form_data = extract_form_data(request, None)
        form_data = json.loads(form_data['body'])
        response_data = form_data['response_data']
        response_data_cp = response_data.copy()

        print("Length of original reponse items: " + str(len(response_data['items'])))

        for i, response in enumerate(response_data['items'][:]):
            try:  # If we parsed a list with email to send emails to
                print(emails)
                email = [e for e in response['answers'] if e['type'] == 'email'][0]['email']

                if email not in emails:
                    print("Email not found")
                    response_data_cp['items'].remove(response)
                else:
                    print("Email found")

            except NameError:  # If we use no list and simply want to use the CRON job
                print("Length of reponse items: " + str(len(response_data['items'])))
                submitted_time = datetime.fromisoformat(response['submitted_at'].replace('Z', '+00:00'))
                curr_time = datetime.now(timezone.utc)

                minutes_diff = (curr_time - submitted_time).total_seconds() / 60.0
                if minutes_diff <= int(CRON_MINS):
                    print(minutes_diff)
                else:
                    response_data_cp['items'].remove(response)

        print("Length of new reponse items: " + str(len(response_data_cp['items'])))
        if len(response_data_cp['items']) == 0:
            reports_sent.append(0)
            continue

        form_data['response_data'] = response_data_cp
        form_data = {
            'body': json.dumps(form_data)
        }

        df = construct_df_from_form_data(form_data, None)

        scores = generate_scores(df, None)

        # Insert class info
        z = scores['body']
        z = json.loads(z)

        z['class_info'] = form_id['class_info']
        scores['body'] = json.dumps(z)
        # End

        pdfs = generate_pdfs(scores, None)

        reports = send_reports(pdfs, None)
        reports = reports['body']
        reports = json.loads(reports)

        reports_sent.append(reports['reports_sent'])

    result = {
        'forms': form_ids,
        'reports_sent': reports_sent
    }

    print(f"Reports sent: {reports_sent}")

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(result)
    }
