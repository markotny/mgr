import pandas as pd
import umap
from elasticsearch import Elasticsearch

es = Elasticsearch()

def get_full_text(id):
    doc = es.get(index='sejm', id=id, _source_includes='treść')
    if doc['found']:
        return doc['_source']['treść']
    else:
        return 'Nie odnaleziono'

def get_embeddings(ids):
    result = es.search(index='sejm', _source_includes='embedding', size=len(ids), body={
        "query": {
            "ids": {
                "values": ids
            }
        }
    })
    return result['hits']['hits']


def remap_embeddings(df, dim):
    embeddings = get_embeddings(df.id.to_list())
    embeddings = [{'id': e['_id'], 'embedding': e['_source']['embedding']}
                  for e in embeddings]
    dfe = pd.DataFrame(embeddings)
    df = pd.merge(df, dfe, on='id')
    mapped = umap.UMAP(n_neighbors=10,
                       n_components=dim,
                       metric='cosine',
                       min_dist=0.0).fit_transform(df.embedding.to_list())
    if dim == 2:
        df['2x'] = mapped[:, 0]
        df['2y'] = mapped[:, 1]
    else:
        df['3x'] = mapped[:, 0]
        df['3y'] = mapped[:, 1]
        df['3z'] = mapped[:, 2]
    return df


def import_data():
    from elasticsearch import helpers
    from tqdm import tqdm
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data_util import load_clean_df, load_embeddings, LEXRANK_WEIGHTED

    df = load_clean_df()

    embeddings = load_embeddings(LEXRANK_WEIGHTED, dim=None)
    df['embedding'] = embeddings

    def to_doc(row):
        return {
            "_index": 'sejm',
            "_id": row.id,
            "_source": row.to_dict()
        }

    docs_gen = (to_doc(row) for index_, row in df.iterrows())

    sejm_settings = {
        "settings" : {
            "max_result_window" : 300000
        },

        "mappings": {
            "properties": {
                "embedding": {"type": "dense_vector", "dims": 768}
            }
        }
    }

    es.indices.create(index='sejm', ignore=400, body=sejm_settings)
    helpers.bulk(es, tqdm(docs_gen, total=len(df)))
