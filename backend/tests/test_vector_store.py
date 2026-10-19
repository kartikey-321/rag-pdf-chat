
import sys
from pathlib import Path

# Allow importing vector_store.py from backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vector_store import search_chunks


def test_anomaly_retrieval():
    doc_id = "1b1defe3-fbfe-4c0e-89a1-ab1e19d76d1e"

    results = search_chunks(
        question="What are the types of anomalies in DBMS?",
        doc_id=doc_id
    )

    context = " ".join(
        doc.page_content.lower() for doc in results
    )

    assert "update anomaly" in context
    assert "insert anomaly" in context
    assert "delete anomaly" in context

def test_document_filtering():
    doc_id = "1b1defe3-fbfe-4c0e-89a1-ab1e19d76d1e"

    results = search_chunks(
        question="What are anomalies in DBMS?",
        doc_id=doc_id
    )

    assert len(results) > 0

    for doc in results:
        assert doc.metadata["document_id"] == doc_id