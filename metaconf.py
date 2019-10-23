
import re
import json
import requests
import click
import keyring
import dateutil.parser

@click.group()
@click.option('--docid', type=int)
@click.pass_context
def cli(ctx, docid):
    ctx.obj['docid'] = docid

def get_auth():
    username = keyring.get_password("issues-cosmos", "username")

    return requests.auth.HTTPBasicAuth(
                username,
                keyring.get_password("issues-cosmos", username),
            )

@cli.command()
@click.pass_context
def pull(ctx):
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}?expand=body.storage".format(docid=ctx.obj['docid']), auth=get_auth())

    body = r.json()['body']['storage']['value']

    open("main.xhtml", "wt").write(body)

@cli.command()
@click.option('--commit', type=bool, default=False, is_flag=True)
@click.pass_context
def push(ctx, commit):
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}?expand=body.storage,version".format(docid=ctx.obj['docid']), auth=get_auth())

    last_version = r.json()['version']
    print(last_version['by']['displayName'])
    print(last_version['when'])

    body = r.json()['body']

    body_storage = open("main.xhtml").read()

    dt = dateutil.parser.parse(last_version['when'])

    updated_body = re.sub("(\|\| updated \|)(.*?)\|","\\1 "+dt.strftime("%Y/%m/%d")+" |", body_storage)

    click.echo(updated_body)

    body['storage']['value'] = updated_body

    headers = {
       "Accept": "application/json",
       "Content-Type": "application/json"
    }
                    
    data = dict(
                version=dict(number=last_version['number']+1),
                title=r.json()['title'],
                type="page",
                body=body,
            )
    
    if commit:
        r=requests.put("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}".format(docid=ctx.obj['docid']), 
                        headers=headers,
                        data=json.dumps(data),
                        auth=get_auth())

        print(r,r.text)

@cli.command()
def history():
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/42242818/history?expand=space,metadata.labels", 
                    auth=get_auth())

    click.echo(r.text)

@cli.command()
@click.pass_context
def versions(ctx):
    headers = {
       "Accept": "application/json"
    }

    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/experimental/content/{docid}/version".format(docid=ctx.obj['docid']), 
                    auth=get_auth(),
                    headers=headers)

    last_version = r.json()['results'][0]

    click.echo(last_version)

if __name__ == "__main__":
    cli(obj={})
