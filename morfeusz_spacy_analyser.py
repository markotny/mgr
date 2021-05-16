import spacy
from data import load_stopwords
import tensorflow as tf
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], enable=True)

class SpacyMorfeuszAnalyser():
    spacy.prefer_gpu()
    nlp = spacy.load('pl_spacy_model_morfeusz', disable=['ner', 'flexer'])

    def __init__(self, ngram_range=(1, 3)):
        self.ngram_range = ngram_range

        self.stop_words = load_stopwords()

        self.ignore_tags = ['interp', 'interj', 'part', 'conj', 'comp', 'pred']

    def _analyse(self, doc):
        org_tokens, lem_tokens = zip(*[(x.text, x.lemma_) for x in doc
                                       if x.lemma_ not in self.stop_words and x.tag_ not in self.ignore_tags])

        return list(lem_tokens) + ngrams(org_tokens, self.ngram_range)

    def __call__(self, text):
        doc = self.nlp(text)
        return self._analyse(doc)


def ngrams(tokens, ngram_range):
    min_n, max_n = ngram_range
    ngrams = []
    n_tokens = len(tokens)

    ngrams_append = ngrams.append
    space_join = " ".join

    for n in range(min_n, max_n + 1):
        for i in range(n_tokens - n + 1):
            ngrams_append(space_join(tokens[i: i + n]))

    return ngrams
