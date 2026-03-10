"""
Matching service for the Lost & Found (ركن البلاغات) feature.

Algorithm (mirrors the mockup's JS logic):
  1. Normalize text (lowercase, strip Arabic diacritics, remove punctuation).
  2. Tokenize, drop stop-words and tokens shorter than 3 characters.
  3. A lost report matches a found report when they share the same category
     OR have at least 1 overlapping token in title/description.
  4. Score = number of overlapping tokens (capped at 4 per field).
  5. Persists new matches in ReportMatch; skips already-existing pairs.
"""

import re
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

# Arabic stop-words to ignore during tokenization
_STOP_WORDS = {
    'في', 'من', 'على', 'عند', 'قرب', 'هذا', 'هذه', 'مع', 'الى', 'إلى',
    'ال', 'و', 'أو', 'لا', 'هو', 'هي', 'أن', 'كان', 'لم', 'قد', 'إن',
}

_DIACRITICS_RE = re.compile(r'[\u064b-\u065f\u0670]')
_NON_WORD_RE = re.compile(r'[^\w\s]', re.UNICODE)


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = _DIACRITICS_RE.sub('', text)
    text = _NON_WORD_RE.sub(' ', text)
    return text


def _tokenize(text: str) -> set:
    tokens = _normalize(text).split()
    return {t for t in tokens if len(t) >= 3 and t not in _STOP_WORDS}


def _overlap_score(tokens_a: set, tokens_b: set, cap: int = 4) -> int:
    return min(len(tokens_a & tokens_b), cap)


def _compute_score(lost, found) -> int:
    """Return a match score >= 1 if they match, else 0."""
    # Category match is an automatic signal
    cat_match = int(lost.category == found.category)

    lost_title_tokens = _tokenize(lost.title)
    found_title_tokens = _tokenize(found.title)
    lost_desc_tokens = _tokenize(lost.description)
    found_desc_tokens = _tokenize(found.description)

    title_score = _overlap_score(lost_title_tokens, found_title_tokens)
    desc_score = _overlap_score(lost_desc_tokens, found_desc_tokens)
    cross_score = _overlap_score(lost_title_tokens, found_desc_tokens) + \
                  _overlap_score(lost_desc_tokens, found_title_tokens)

    total = cat_match + title_score + desc_score + cross_score
    return total


def find_matches_for_report(report):
    """
    Given a newly approved report, find all matches with reports of the
    opposite type. Creates ReportMatch rows for new matches only.

    Returns the number of new matches created.
    """
    from marketplace.models.lost_found import Report, ReportMatch

    if report.type == Report.TYPE_LOST:
        candidates = Report.objects.filter(
            type=Report.TYPE_FOUND,
            status=Report.STATUS_ACTIVE,
            is_deleted=False,
        ).exclude(
            # skip already matched
            matches_as_found__lost_report=report,
        )
        lost = report
        get_lost_found = lambda c: (lost, c)
    else:
        candidates = Report.objects.filter(
            type=Report.TYPE_LOST,
            status=Report.STATUS_ACTIVE,
            is_deleted=False,
        ).exclude(
            matches_as_lost__found_report=report,
        )
        found = report
        get_lost_found = lambda c: (c, found)

    new_matches = 0
    matches_to_create = []

    for candidate in candidates:
        lost_r, found_r = get_lost_found(candidate)
        score = _compute_score(lost_r, found_r)
        if score > 0:
            matches_to_create.append(
                ReportMatch(lost_report=lost_r, found_report=found_r, score=score)
            )

    if matches_to_create:
        with transaction.atomic():
            created = ReportMatch.objects.bulk_create(
                matches_to_create, ignore_conflicts=True
            )
            new_matches = len(created)

    logger.info(
        "Lost & Found matching: report #%s (%s) → %d new match(es)",
        report.pk, report.type, new_matches,
    )
    return new_matches
