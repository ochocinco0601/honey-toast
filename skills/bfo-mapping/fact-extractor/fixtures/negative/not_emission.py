# Negative control - constructs that must NOT be read as emission sites.
# Each one is a discriminator the emission rules depend on. A match here is a regression.

from collections import Counter

# `collections.Counter` over an iterable. Same name as the prometheus_client metric and
# nothing to do with emitting anything. The rules require a name-and-help pair of string
# literals, which this does not have.
word_freq = Counter(words)
empty_tally = Counter()
from_pairs = Counter({"a": 1, "b": 2})


# A single string argument is still not a metric declaration - prometheus_client requires
# the help text, so one literal must not be enough to match.
one_arg = Counter("just-a-label")
