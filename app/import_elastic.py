from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data import load_file, load_clean_df, load_embeddings, LEXRANK_WEIGHTED

# curl -XPUT -H 'Content-Type: application/json' 'localhost:9200/_settings' -d '
# {
#     "index" : {
#         "number_of_replicas" : 0
#     }
# }'

def import_sejm_data():
    es = Elasticsearch()
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

def import_topic_data():
    es = Elasticsearch()
    df = load_file('topics_desc.pkl')

    df['wagi'] = [[w[1] for w in words] for words in df.words]
    df['words'] = [[w[0] for w in words] for words in df.words]
    df.rename(columns={"words": "słowa", "desc": "opis"}, inplace=True)
    
    def to_doc(index, row):
        return {
            "_index": 'tematy',
            "_id": index,
            "_source": row.to_dict()
        }

    docs_gen = (to_doc(index, row) for index, row in df.iterrows())

    tematy_settings = {
        "mappings": {
            "properties": {
                "embedding": {"type": "dense_vector", "dims": 768}
            }
        }
    }

    es.indices.create(index='tematy', ignore=400, body=tematy_settings)
    helpers.bulk(es, tqdm(docs_gen, total=len(df)))

# import_sejm_data()
import_topic_data()