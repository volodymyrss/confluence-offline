
import requests
import click
import keyring

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
def getbody(ctx):
    r=requests.get("https://issues.cosmos.esa.int/socciwiki/rest/api/content/{docid}?expand=body".format(docid=ctx.obj['docid']), auth=get_auth())

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

    last_version = r.json()['results'][0]

    click.echo(last_version)

if __name__ == "__main__":
    cli(obj={})
