from unittest import result
import requests
import time
from datetime import date

# github repository username and repository https://github.com/<username>/<repository>/blob/main/README.md
github_username=''

# wich app selected in notion properties will push to this repo
app_to_repo = ''

github_repository=''
# branch from which the new is created
github_base_branch=''

# github > settings > developper setting > personal access tokens
github_token=''

# Database id https://www.notion.so/<user>/<database_id>?v=656a93c4382740d5abb9a4c2295a0ecf
notion_database_id=''

# notion workspace > Settings & members > integrations > internal integration_name '...' > Copy internal integration token
notion_integration_token=''

# the only one column who will trigger new branch
notion_board_column=''

logs_path="/var/log/bot_notion_back.log"

today = date.today()

def create_branch(branch_name):
    headers = {'Authorization': "Token " + github_token}
    url = f"https://api.github.com/repos/{github_username}/{github_repository}/git/refs/heads"
    branches = requests.get(url, headers=headers).json()
    branch_sha=''
    for index, branch in enumerate(branches):
        if branch['ref'] == f'refs/heads/{github_base_branch}':
            branch_sha=branch['object']['sha']
    branch, sha = branches[-1]['ref'], branches[-1]['object']['sha']
    branch = 'refs/heads/staging'
    res = requests.post(f'https://api.github.com/repos/{github_username}/{github_repository}/git/refs', json={
        "ref": f"refs/heads/{branch_name}",
        "sha": branch_sha,
        "head": 'main'
    }, headers=headers)

def get_branches():
    headers = {'Authorization': "Token " + github_token}
    url = f"https://api.github.com/repos/{github_username}/{github_repository}/git/refs/heads"
    branches = requests.get(url, headers=headers).json()\
    
    resp_branches = []
    for branch in branches:
        resp_branches.append(branch['ref'].split('/')[-1])

    return resp_branches

def get_tickets_from_notion():
  url = f'https://api.notion.com/v1/databases/{notion_database_id}/query'

  r = requests.post(url, headers={
    "Authorization": f"Bearer {notion_integration_token}",
    "Notion-Version": "2021-05-13"
  })
  
  if r.status_code != 200:
    return {'status_code':r.status_code,'result':r}
  else:      
    result_dict = r.json()
    result = result_dict['results']

    tickets_in_columnm= []

    # select tickets in specified notion column
    for ticket in result:
        if 'Status' in ticket['properties']:
            if ticket['properties']['Status']['select']['name'] == notion_board_column:
                apps = ticket['properties']['App']['multi_select']
                apps_names = []
                for app in apps:
                    apps_names.append(app['name'])
                if app_to_repo in apps_names:
                    tickets_in_columnm.append({'ticket': ticket['properties']})


    titles=[]

    for ticket in tickets_in_columnm:
        ticket_name = ticket['ticket']['Name']['title'][0]['plain_text']
        titles.append(ticket_name.strip().replace(" ", "-").lower())
        
    return {'status_code':r.status_code,'result':titles}

def update_branches_with_tickets(tickets, branches):
    for ticket in tickets:
        if ticket not in branches:
            create_branch(ticket)
            write_log(f'Branch {ticket} created')

        else:
            write_log(f'Branch {ticket} already exists')
        
def write_log(content):
    print('entro a la funcion')
    with open(logs_path, "a") as f:
        print(today.strftime("%d/%m/%Y") +" | "+ content + "\n")
        f.write(today.strftime("%d/%m/%Y") +" | "+ content + "\n")


notion_tickets = get_tickets_from_notion()
if notion_tickets['status_code'] == 200:
    github_branches = get_branches()

    update_branches_with_tickets(notion_tickets['result'],github_branches)
else:
    write_log('Notion error')