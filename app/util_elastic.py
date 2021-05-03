import pandas as pd
import umap
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

es = Elasticsearch()
model = SentenceTransformer("xlm-r-distilroberta-base-paraphrase-v1")


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


def _cosine_search(index, query, size=10, min_score=None):
    embedding = model.encode(query)

    query = {
        "script_score": {
            "query": {
                "match_all": {}
            },
            "script": {
                "source": "cosineSimilarity(params.query, 'embedding') + 1.0",
                "params": {
                    "query": embedding
                }
            }
        }
    }
    if min_score is not None:
        body = {
            "min_score": min_score + 1.0,
            "query": query
        }
    else:
        body = {"query": query}
    result = es.search(index=index, _source=False, size=size, body=body)
    return result['hits']['hits']


def search_speeches(query, threshold):
    return _cosine_search('sejm', query, 10000, threshold)


def search_topics(query):
    return _cosine_search('tematy', query)


def get_topic_dict():
    result = es.search(index="tematy", _source_includes='opis', size=1000, body={
        "query": {
            "match_all": {}
        }})
    topics = result['hits']['hits']
    topic_dict = {t['_id']: t['_source']['opis'] for t in topics}
    return topic_dict


def remap_embeddings(df, dim, n_neighbors=10):
    embeddings = get_embeddings(df.id.to_list())
    embeddings = [{'id': e['_id'], 'embedding': e['_source']['embedding']}
                  for e in embeddings]
    dfe = pd.DataFrame(embeddings)
    df = pd.merge(df, dfe, on='id')
    mapped = umap.UMAP(n_neighbors=n_neighbors,
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
