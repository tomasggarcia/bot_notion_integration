import requests

# github repository username and repository https://github.com/<username>/<repository>/blob/main/README.md
github_username=''
github_repository=''
# branch from which the new is created
github_base_branch=''

# github > settings > developper setting > personal access tokens
github_token=''

# Database id https://www.notion.so/<user>/<database_id>?v=656a93c4382740d5abb9a4c2295a0ecf
notion_database_id=''

# notion workspace > Settings & members > integrations > internal integration_name '...' > Copy internal integration token
notion_integration_token=''

notion_board_column=''

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
  result_dict = r.json()
  result = result_dict['results']

  tickets = []
  
  tickets_in_columnm= []
  for i in result:
      if 'Status' in i['properties']:
          if i['properties']['Status']['select']['name'] == notion_board_column:
            tickets_in_columnm.append({'ticket': i['properties']})

  titles=[]

  for ticket in tickets_in_columnm:
    ticket_name = ticket['ticket']['Name']['title'][0]['plain_text']
    titles.append(ticket_name.strip().replace(" ", "-").lower())
    
  return titles

def update_branches_with_tickets(tickets, branches):
    for ticket in tickets:
        if ticket not in branches:
            create_branch(ticket)
            print(f'Branch {ticket} created')
        else:
            print(f'Branch {ticket} already exists')
        


notion_tickets = get_tickets_from_notion()

github_branches = get_branches()

update_branches_with_tickets(notion_tickets,github_branches)
