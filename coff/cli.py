import re
import yaml
import json
import requests
import click
import keyring
import dateutil.parser
import html2text

import subprocess
    

def get_git_reference():
    try:
        return (subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip(),
                subprocess.check_output(["git", "describe", "--tags", "--always"]).decode().strip())
    except Exception as e:
        click.echo("failed to get git reference: %s"%repr(e))

@click.group()
@click.option('--docid', type=int)
@click.option('--store-config', type=bool, default=False, is_flag=True)
@click.pass_context
def cli(ctx, docid, store_config):
    yfn = "confluence.yaml"

    if docid is None:
        docid = yaml.load(open(yfn))['docid']
        click.echo("loading docid from {yfn}: {docid}".format(yfn=yfn, docid=docid))

    ctx.obj['docid'] = docid

    if store_config:
        yaml.dump(dict(docid=docid), open(yfn, "wt"))

def get_auth():
    username = keyring.get_password("issues-cosmos", "username")

    return requests.auth.HTTPBasicAuth(
                username,
                keyring.get_password("issues-cosmos", username),
            )

@cli.command()
@click.pass_context
@click.option("--text", type=bool, default=True)
def pull(ctx, text):
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}?expand=body.storage".format(docid=ctx.obj['docid']), auth=get_auth())

    body = r.json()['body']['storage']['value']

    open("main.xhtml", "wt").write(body)

    if text:
        open("main.txt", "wt").write(html2text.html2text(body))

@cli.command()
@click.option('--commit', type=bool, default=False, is_flag=True)
@click.pass_context
def push(ctx, commit):
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}?expand=body.storage,version".format(docid=ctx.obj['docid']), auth=get_auth())

    last_version = r.json()['version']
    click.echo(last_version['by']['displayName'])
    click.echo(last_version['when'])

    body = r.json()['body']

    body_storage = open("main.xhtml").read()

    dt = dateutil.parser.parse(last_version['when'])

    updated_body = re.sub("(\|\| updated \|)(.*?)\|","\\1 "+dt.strftime("%Y/%m/%d")+" |", body_storage)
    
    git_remote, git_reference = get_git_reference()

    if git_reference is not None:
        updated_body = re.sub("(\|\| AKA \|)(.*?)\|","\\1 " + git_remote +  " @ "+git_reference+" |", updated_body)

    click.echo(updated_body)

    body['storage']['value'] = updated_body

    commit_message = "metadata sync"

    headers = {
       "Accept": "application/json",
       "Content-Type": "application/json"
    }
                    
    data = dict(
                version=dict(number=last_version['number']+1, minorEdit=True, message=commit_message),
                title=r.json()['title'],
                type="page",
                body=body,
            )
    
    if commit:
        r=requests.put("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}".format(docid=ctx.obj['docid']), 
                        headers=headers,
                        data=json.dumps(data),
                        auth=get_auth())

        click.echo(r.text)

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

    for version in r.json()['results']:
        click.echo((version['number'], version['by']['displayName'], version['when']))

def main():
    cli(obj={})

if __name__ == "__main__":
    main()

