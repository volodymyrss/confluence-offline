import logging
import re
import yaml
import json
import requests
import click
import keyring
import dateutil.parser
import html2text
# import dynaconf

# dynaconf.Dynaconf()

import subprocess
    
logger = logging.getLogger(__name__)

def get_git_reference():
    try:
        return (subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip(),
                subprocess.check_output(["git", "describe", "--tags", "--always"]).decode().strip())
    except Exception as e:
        click.echo("failed to get git reference: %s"%repr(e))

@click.group()
@click.option('-d', '--debug', is_flag=True)
@click.option('--docid', type=int)
@click.option('--store-config', type=bool, default=False, is_flag=True)
@click.pass_context
def cli(ctx, debug, docid, store_config):
    if debug:
        logging.basicConfig(level="DEBUG")
    else:
        logging.basicConfig(level="INFO")

    yfn = "confluence.yaml"

    cfg = yaml.load(open(yfn), Loader=yaml.SafeLoader)

    if docid is None:
        docid = cfg['docid']
        click.echo("loading docid from {yfn}: {docid}".format(yfn=yfn, docid=docid))

    for k, v in cfg.items():
        ctx.obj[k] = v

    ctx.obj['docid'] = docid
    ctx.obj['base_url'] = cfg.get('base_url', 'https://issues.cosmos.esa.int/socciwiki/rest/api')

    if store_config:
        yaml.dump(dict(docid=docid), open(yfn, "wt"))

def get_auth(site="issues-cosmos"):
    logging.info("will find username for site %s", site)
    username = keyring.get_password(site, "username")

    logging.info("will find password for user %s", username)

    return requests.auth.HTTPBasicAuth(
                username,
                keyring.get_password(site, username),
            )


def get_headers(ctx):
    return {
       "Authorization": f"Bearer {keyring.get_password(ctx.obj['site'], 'pat')}",
       "Accept": "application/json",
       "Content-Type": "application/json",
    }


@cli.command()
@click.pass_context
@click.option("--text", type=bool, default=True)
def pull(ctx, text):
        
    r = requests.get("{base_url}/content/{docid}?expand=body.storage".format(
                      base_url=ctx.obj['base_url'], 
                      docid=ctx.obj['docid']), 
                      headers=get_headers(ctx))

    logger.warning("%s: %s", r, r.text)

    body = r.json()['body']['storage']['value']

    open("main.xhtml", "wt").write(body)

    if text:
        open("main.txt", "wt").write(html2text.html2text(body))


@cli.command()
@click.option('--commit', type=bool, default=False, is_flag=True)
@click.option('-m', '--message', type=str)
@click.pass_context
def push(ctx, commit, message):
                  
    r = requests.get(f"{ctx.obj['base_url']}/content/{ctx.obj['docid']}?expand=body.storage,version",
                     headers=get_headers(ctx))

    logger.info("response: %s %s", r, r.text)

    last_version = r.json()['version']
    logger.info("last version: %s", last_version['by']['displayName'])
    logger.info("            : %s", last_version['when'])

    body = r.json()['body']

    body_storage = open("main.xhtml").read()

    dt = dateutil.parser.parse(last_version['when'])

    updated_body = re.sub("(\|\| updated \|)(.*?)\|","\\1 "+dt.strftime("%Y/%m/%d")+" |", body_storage)
    
    git_remote, git_reference = get_git_reference()

    if git_reference is not None:
        updated_body = re.sub("(\|\| AKA \|)(.*?)\|","\\1 " + git_remote +  " @ "+git_reference+" |", updated_body)

    click.echo(updated_body)

    body['storage']['value'] = updated_body

    commit_message = message
     
    data = dict(
                version=dict(number=last_version['number']+1, minorEdit=True, message=commit_message),
                title=r.json()['title'],
                type="page",
                body=body,
            )
    
    if commit:
        r=requests.put(f"{ctx.obj['base_url']}/content/{ctx.obj['docid']}", 
                        headers=get_headers(ctx),
                        data=json.dumps(data))

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

