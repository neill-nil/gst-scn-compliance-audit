"""A small Okapi BM25 index in pure Python (no numpy), shared by statute and case-law search."""
import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("the of and to in a or for by any be is under as such shall on with which that this from has been "
           "an at not are it its other was were if no than may into".split())


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(tokenize(d)) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df = Counter(t for c in self.tf for t in c)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.postings: dict[str, list[int]] = {}
        for i, c in enumerate(self.tf):
            for t in c:
                self.postings.setdefault(t, []).append(i)

    def search(self, query: str, k: int = 5) -> list[tuple[int, float]]:
        scores: Counter = Counter()
        for t in set(tokenize(query)):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i in self.postings[t]:
                f = self.tf[i][t]
                scores[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return scores.most_common(k)
