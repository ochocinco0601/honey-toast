"""The one rule for comparing file paths across the kit's checks, and whether opened line spans cover a citation.

A path from a transcript, a citation or the code reader is compared only after `norm`: forward slashes, lower case,
no trailing slash. Python standard library only."""


def norm(p):
    return str(p).replace("\\", "/").lower().rstrip("/")


def covered(first, last, spans):
    """Lines first..last are all inside the (a, b) spans taken together; a citation with no line (first None) needs
    any span at all."""
    if first is None:
        return bool(spans)
    line = first
    while line <= last:
        nxt = max((b for a, b in spans if a <= line <= b), default=None)
        if nxt is None:
            return False
        line = nxt + 1
    return True
