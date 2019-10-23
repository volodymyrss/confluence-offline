# Offline editing and metadata syncing for Confluence 

```bash
# fetch the document, store current doc ID
co --store-config --docid=42242818 pull
# explore versions
co versions
# edit the doc
vim main.xhtml
# push back, also update the metadata
co push --commit
```
