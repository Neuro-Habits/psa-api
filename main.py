import sys
sys.path.append('../functions')

from app import *
import json

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

form_ids = []

form_ids.append({
    'form_id':fetch_form_id('Education', 'dev', init_info),
    'class_info':education_info
})
form_ids.append({
    'form_id':fetch_form_id('Vitality', 'dev', init_info),
    'class_info':vitality_info
})

print(form_ids)

form_id = form_ids[0]
print(form_id)

# %%

event = json.dumps({'form_id':form_id['form_id']}) # Education
# event = json.dumps({'form_id':'vaXpvkUJ'}) # Stress

form_data = extract_form_data(event,None)
form_data

# %%

event = form_data
form_df = construct_df_from_form_data(event,None)
form_df

# %%

event = form_df
scores = generate_scores(event, None)
scores

# %%

data = scores['body']
data = json.loads(data)

data['class_info'] = form_id['class_info']
scores['body'] = json.dumps(data)

event = generate_pdfs(scores, None)
# event

# %%

send_emails(event, None)

# %%

selfscan_cron(None,None)