MODULE_PATH = "./BERTopic/bertopic/__init__.py"
MODULE_NAME = "bertopic"
import importlib
import sys
spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module 
spec.loader.exec_module(module)

from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
import hdbscan


def create_model(min_cluster_size=20, min_samples=None, ngram_range=(1,3), test_sample=None, test_sample_frac=None):
    with open('polish_stopwords.txt') as f:
        stop_words = [x.strip() for x in f]

    vectorizer_model = CountVectorizer(stop_words=stop_words, ngram_range=ngram_range, min_df=5)

    sentence_model = SentenceTransformer("xlm-r-distilroberta-base-paraphrase-v1")

    if min_samples is None:
        min_samples = min_cluster_size

    hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)

    topic_model = BERTopic(
        embedding_model=sentence_model,
        vectorizer_model=vectorizer_model,
        hdbscan_model=hdbscan_model,
        low_memory=True,
        verbose=True,
        test_sample=test_sample,
        test_sample_frac=test_sample_frac)

    return topic_model