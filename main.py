import sys
sys.path.append('../functions')
from config import *

# %%

form_ids = []

form_ids.append({
    'form_id':fetch_form_id('Vitality HLR', 'prod', init_info),
    'class_info':vitalityHLR_info
})
form_ids.append({
    'form_id':fetch_form_id('Vitality Ichtus', 'prod', init_info),
    'class_info':vitalityHLR_info
})
print(form_ids)
form_id = form_ids[0]

# %%

event = json.dumps({'form_info':form_id})
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