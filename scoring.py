import re
import pandas as pd
from bertopic_model import create_model
import numpy as np
import gensim.corpora as corpora
from gensim.models.coherencemodel import CoherenceModel
from timeit import default_timer as timer
import hdbscan
import logging

NGRAM_RANGE = (1, 2)
MIN_TEST_SAMPLE = 100
TEST_SAMPLE_FRAC = 0.2


def score_coherence(docs, embeddings, min_cluster_size, min_samples):
    topics_all = _check_topics(embeddings, min_cluster_size, min_samples)
    if topics_all.max() > 1000 or topics_all.max() < 20:
        logging.warning(f'{topics_all.max()} topics - aborting')
        return None, None, None, None, topics_all, (topics_all == -1).sum(), None

    topic_words, tokens, topics, topics_all = _prepare_bertopic(
        docs, embeddings, min_cluster_size, min_samples)

    top, count = np.unique(topics, return_counts=True)
    not_found = count[np.where(top == -1)][0]
    logging.info('total: {}, with topics: {}, topics: {}'.format(
        len(topics), len(topics) - not_found, len(top)))

    not_found = (topics_all == -1).sum()
    logging.info(f'not found: {not_found} ({not_found / len(topics_all)})')

    dictionary = corpora.Dictionary(tokens)

    corpus = [dictionary.doc2bow(token) for token in tokens]

    start = timer()
    score_u_mass = _score(topic_words, tokens, corpus,
                          dictionary, coherence='u_mass')
    logging.info(f'scored u_mass in {timer() - start}')

    score_c_v = _score(topic_words, tokens, corpus,
                       dictionary, coherence='c_v')
    logging.info(f'scored c_v in {timer() - start}')

    score_c_uci = _score(topic_words, tokens, corpus,
                       dictionary, coherence='c_uci')
    logging.info(f'scored c_uci in {timer() - start}')

    score_c_npmi = _score(topic_words, tokens, corpus,
                       dictionary, coherence='c_npmi')
    logging.info(f'scored c_npmi in {timer() - start}')

    logging.info(f'scored all. Took: {timer() - start}')
    return score_c_v, score_u_mass, score_c_uci, score_c_npmi, topics_all, not_found, len(topics)


def _check_topics(umap_embeddings, min_cluster_size, min_samples):
    hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples).fit(umap_embeddings)
    topics = hdbscan_model.labels_
    return topics

def _prepare_bertopic(docs, umap_embeddings, min_cluster_size, min_samples):
    topic_model = create_model(
        min_cluster_size, min_samples, NGRAM_RANGE, MIN_TEST_SAMPLE, TEST_SAMPLE_FRAC)

    topics, _, documents = topic_model.fit_transform(
        docs, umap_embeddings=umap_embeddings)

    topics_all = topic_model.hdbscan_model.labels_

    # Preprocess Documents - ignore not found documents for coherence scoring
    documents_per_topic = documents[documents.Topic != -1].groupby(
        ['Topic'], as_index=False).agg({'Document': ' '.join})

    # Extract vectorizer and analyzer from BERTopic
    vectorizer = topic_model.vectorizer_model
    analyzer = vectorizer.build_analyzer()

    # Extract features for Topic Coherence evaluation
    tokens = [analyzer(doc) for doc in topic_model._preprocess_text(
        documents_per_topic.Document.values)]
    topic_words = [[words for words, _ in topic_model.get_topic(topic)]
                   for topic in documents_per_topic.Topic.values]

    return topic_words, tokens, topics, topics_all


def _score(topic_words, tokens, corpus, dictionary, coherence='c_v'):
    coherence_model = CoherenceModel(topics=topic_words,
                                     texts=tokens,
                                     corpus=corpus,
                                     dictionary=dictionary,
                                     coherence=coherence)
    coherence = coherence_model.get_coherence()

    return coherence


# mode = count_unknown | skip_unknown
def score_consistency(df, topics, mode='skip_unknown'):
    df['topic'] = topics
    df['speech_order'] = [
        int(re.search(r".+div-(\d+)", doc_id).groups()[0]) for doc_id in df['id']]
    same_per_day = []
    different_per_day = []
    topics_per_day = []

    for _, day in df.sort_values('speech_order').groupby(by='date'):
        if len(day) < 2:
            continue

        same = 0
        different = 0
        for i in range(len(day) - 1):
            if mode == 'skip_unknown' and day.iloc[i].topic == -1:
                continue
            if day.iloc[i].topic == day.iloc[i + 1].topic:
                same += 1
            else:
                different += 1

        topics = len(day.topic.unique())
        different -= (topics - 1)

        same_per_day.append(same)
        different_per_day.append(different)
        topics_per_day.append(topics)

    score = np.sum(same_per_day) / np.sum([*same_per_day, *different_per_day])

    return score
