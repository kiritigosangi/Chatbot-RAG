"""Closed corpus: PRD §9 / source brief only. 25 URLs. No substitutes."""

from __future__ import annotations

from typing import Literal, TypedDict

Scheme = Literal[
    "large_cap",
    "flexicap",
    "elss",
    "midcap",
    "small_cap",
    "house",
    "regulatory",
]

DocType = Literal[
    "scheme_page",
    "sid",
    "kim",
    "factsheet",
    "ter",
    "sai",
    "tax",
    "repository",
    "sebi",
    "amfi",
]


class Source(TypedDict):
    source_id: int
    url: str
    scheme: Scheme
    doc_type: DocType
    title: str
    document_date: str | None


# Exact URLs from RAG Chatbot.txt. IDs 1–25. Do not add or swap URLs here
# without a PRD update.
SOURCES: tuple[Source, ...] = (
    {
        "source_id": 1,
        "url": "https://www.indmoney.com/mutual-funds/sbi-large-cap-fund-direct-growth",
        "scheme": "large_cap",
        "doc_type": "scheme_page",
        "title": "SBI Large Cap Fund Direct Growth (INDmoney)",
        "document_date": None,
    },
    {
        "source_id": 2,
        "url": "https://www.indmoney.com/mutual-funds/sbi-flexicap-fund-direct-growth",
        "scheme": "flexicap",
        "doc_type": "scheme_page",
        "title": "SBI Flexicap Fund Direct Growth (INDmoney)",
        "document_date": None,
    },
    {
        "source_id": 3,
        "url": "https://www.indmoney.com/mutual-funds/sbi-elss-tax-saver-fund-direct-growth",
        "scheme": "elss",
        "doc_type": "scheme_page",
        "title": "SBI ELSS Tax Saver Fund Direct Growth (INDmoney)",
        "document_date": None,
    },
    {
        "source_id": 4,
        "url": "https://www.indmoney.com/mutual-funds/sbi-midcap-fund-direct-growth",
        "scheme": "midcap",
        "doc_type": "scheme_page",
        "title": "SBI Midcap Fund Direct Growth (INDmoney)",
        "document_date": None,
    },
    {
        "source_id": 5,
        "url": "https://www.indmoney.com/mutual-funds/sbi-small-cap-fund-direct-plan-growth",
        "scheme": "small_cap",
        "doc_type": "scheme_page",
        "title": "SBI Small Cap Fund Direct Growth (INDmoney)",
        "document_date": None,
    },
    {
        "source_id": 6,
        "url": "https://www.sbimf.com/docs/default-source/scheme-portfolios/default-library/sid---sbi-bluechip-fund1d0cd92660064395ab092fb9e5ee7c79.pdf",
        "scheme": "large_cap",
        "doc_type": "sid",
        "title": "SBI BlueChip Fund SID",
        "document_date": None,
    },
    {
        "source_id": 7,
        "url": "https://www.sbimf.com/docs/default-source/default-library/kim---sbi-blue-chip-fund32655f1826bd4e598e32b00e729fb603.pdf",
        "scheme": "large_cap",
        "doc_type": "kim",
        "title": "SBI BlueChip Fund KIM",
        "document_date": None,
    },
    {
        "source_id": 8,
        "url": "https://www.sbimf.com/docs/default-source/default-library/sid---sbi-flexicap-fund6c696fdab92a47019f5c32d91c967d62.pdf",
        "scheme": "flexicap",
        "doc_type": "sid",
        "title": "SBI Flexicap Fund SID",
        "document_date": None,
    },
    {
        "source_id": 9,
        "url": "https://www.sbimf.com/docs/default-source/default-library/kim---sbi-flexicap-fund0bc48eb83bf949309a7d16b37b3031b0.pdf",
        "scheme": "flexicap",
        "doc_type": "kim",
        "title": "SBI Flexicap Fund KIM",
        "document_date": None,
    },
    {
        "source_id": 10,
        "url": "https://www.sbimf.com/docs/default-source/scheme-portfolios/default-library/sid---sbi-long-term-equity-fund386480308ef94fa0b9113c8f2911e7f8.pdf",
        "scheme": "elss",
        "doc_type": "sid",
        "title": "SBI Long Term Equity / ELSS SID",
        "document_date": None,
    },
    {
        "source_id": 11,
        "url": "https://www.sbimf.com/docs/default-source/lists/sid_kim/sid---sbi-small-cap-fund.pdf",
        "scheme": "small_cap",
        "doc_type": "sid",
        "title": "SBI Small Cap Fund SID",
        "document_date": None,
    },
    {
        "source_id": 12,
        "url": "https://www.sbimf.com/docs/default-source/sif-forms/kim---sbi-small-cap-fund.pdf",
        "scheme": "small_cap",
        "doc_type": "kim",
        "title": "SBI Small Cap Fund KIM",
        "document_date": None,
    },
    {
        "source_id": 13,
        "url": "https://www.sbimf.com/docs/default-source/default-library/sid---sbi-magnum-midcap-fund2a5c652f53c14e80b25de06be5cb228e.pdf",
        "scheme": "midcap",
        "doc_type": "sid",
        "title": "SBI Magnum Midcap Fund SID",
        "document_date": None,
    },
    {
        "source_id": 14,
        "url": "https://www.sbimf.com/docs/default-source/scheme-factsheets/sbi-elss-tax-saver-fund-factsheet-january-2026.pdf",
        "scheme": "elss",
        "doc_type": "factsheet",
        "title": "SBI ELSS Tax Saver Fund factsheet January 2026",
        "document_date": "January 2026",
    },
    {
        "source_id": 15,
        "url": "https://www.sbimf.com/docs/default-source/scheme-factsheets/all-sbimf-schemes-factsheet-february-2026.pdf",
        "scheme": "house",
        "doc_type": "factsheet",
        "title": "SBI MF all-schemes comparative factsheet February 2026",
        "document_date": "February 2026",
    },
    {
        "source_id": 16,
        "url": "https://www.sbimf.com/docs/default-source/scheme-factsheets/all-sbimf-schemes-factsheet-january-2026.pdf",
        "scheme": "house",
        "doc_type": "factsheet",
        "title": "SBI MF all-schemes Direct Plan factsheet January 2026",
        "document_date": "January 2026",
    },
    {
        "source_id": 17,
        "url": "https://www.sbimf.com/total-expense-ratio",
        "scheme": "house",
        "doc_type": "ter",
        "title": "SBI Mutual Fund Total Expense Ratio",
        "document_date": None,
    },
    {
        "source_id": 18,
        "url": "https://www.sbimf.com/docs/default-source/documents/statement-of-additional-information.pdf",
        "scheme": "house",
        "doc_type": "sai",
        "title": "SBI Mutual Fund Statement of Additional Information",
        "document_date": None,
    },
    {
        "source_id": 19,
        "url": "https://www.sbimf.com/docs/default-source/pdf/sbi-mf-tax-reckoner-fy-2026-27.pdf",
        "scheme": "house",
        "doc_type": "tax",
        "title": "SBI MF Tax Reckoner FY 2026–27",
        "document_date": "FY 2026–27",
    },
    {
        "source_id": 20,
        "url": "https://www.sbimf.com/offer-document-sid-kim",
        "scheme": "house",
        "doc_type": "repository",
        "title": "SBI MF SID / KIM repository",
        "document_date": None,
    },
    {
        "source_id": 21,
        "url": "https://www.sebi.gov.in/filings/mutual-funds.html",
        "scheme": "regulatory",
        "doc_type": "sebi",
        "title": "SEBI mutual fund filings",
        "document_date": None,
    },
    {
        "source_id": 22,
        "url": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doGetFundDetails=yes&mfId=49&type=3",
        "scheme": "regulatory",
        "doc_type": "sebi",
        "title": "SEBI SBI Mutual Fund filings",
        "document_date": None,
    },
    {
        "source_id": 23,
        "url": "https://www.sebi.gov.in/web/?file=https%3A%2F%2Fwww.sebi.gov.in%2Fsebi_data%2Fattachdocs%2Ffeb-2026%2F1772079826878.pdf",
        "scheme": "regulatory",
        "doc_type": "sebi",
        "title": "SEBI mutual fund scheme categorisation (Feb 2026)",
        "document_date": "February 2026",
    },
    {
        "source_id": 24,
        "url": "https://www.sebi.gov.in/sebi_data/mutualfundfile/dec-2024/1734347478952.pdf",
        "scheme": "regulatory",
        "doc_type": "sebi",
        "title": "SEBI SBI Mutual Fund disclosure document",
        "document_date": "December 2024",
    },
    {
        "source_id": 25,
        "url": "https://portal.amfiindia.com/spages/4675.pdf",
        "scheme": "regulatory",
        "doc_type": "amfi",
        "title": "AMFI SBI Mutual Fund scheme document",
        "document_date": None,
    },
)

ALLOWED_URLS: frozenset[str] = frozenset(s["url"] for s in SOURCES)


def get_source(source_id: int) -> Source:
    for source in SOURCES:
        if source["source_id"] == source_id:
            return source
    raise KeyError(f"source_id {source_id} is not in the closed corpus (1–25)")


def assert_closed_corpus() -> None:
    ids = [s["source_id"] for s in SOURCES]
    if ids != list(range(1, 26)):
        raise RuntimeError("Allowlist must be exactly source_id 1 through 25")
    if len(ALLOWED_URLS) != 25:
        raise RuntimeError("Allowlist URLs must be unique and exactly 25")
