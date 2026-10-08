import pytest
import xml.etree.ElementTree as ET
from src.adapters.outbound.study_schema_exporter_adapter import StudySchemaExporterAdapter
from src.core.domain.models import StudyArtifact

SAMPLE_MARKDOWN = """
# Lecture 1: Advanced Microeconomics

Some lecture text introducing consumer choice and duality.

---
## 🧠 Conceptual Architecture & Relational Graphs
```mermaid
mindmap
  root((Consumer Choice))
    Axioms of Preference
      Completeness
      Transitivity
    Utility Maximization
      Marshallian Demand
      Indirect Utility Function
    Expenditure Minimization
      Hicksian Demand
      Expenditure Function
```

```mermaid
graph TD
  Shock[Price Shock dp_i] --> Sub[Substitution Effect: Negative Semidefinite]
  Shock --> Inc[Income Effect: Normal vs Inferior]
  Sub --> Total[Slutsky Equation Decomposition]
  Inc --> Total
```

---
## 🎯 Active Recall & Examination Drills
- **Drill 1 (Foundational):** What is the necessary condition for preferences to be represented by a continuous utility function?
  * **Rubric:** Mention Debreu's Representation Theorem, continuity, and complete pre-order.
- **Drill 2 (Analytical):** Prove Roy's Identity using the Envelope Theorem.
  * **Rubric:** State $v(p, w) = \\max u(x) \\text{ s.t. } p \\cdot x \\le w$, apply Envelope Theorem with respect to $p_i$ and $w$.

---
## ⚖️ Model Boundary Conditions
| Model / Framework | Validity Domain | Failure Trigger / Invalidation | Robust Alternative |
| :--- | :--- | :--- | :--- |
| Utility Maximization | Convex, monotonic preferences | Non-convex budget sets | Discrete choice models |
| Slutsky Symmetry | Differentiable demand | Corner solutions / kinks | Revealed Preference Weak Axiom |
""".strip()


def test_extract_artifacts_full_markdown():
    adapter = StudySchemaExporterAdapter()
    artifact = adapter.extract_artifacts(SAMPLE_MARKDOWN, "hash_123", "Microeconomics")

    assert artifact.document_hash == "hash_123"
    assert artifact.title == "Microeconomics"
    assert artifact.mindmap_mermaid is not None
    assert "mindmap" in artifact.mindmap_mermaid
    assert "Axioms of Preference" in artifact.mindmap_mermaid

    assert artifact.flowchart_mermaid is not None
    assert "graph TD" in artifact.flowchart_mermaid
    assert "Slutsky Equation" in artifact.flowchart_mermaid

    assert artifact.active_recall_markdown is not None
    assert "Active Recall" in artifact.active_recall_markdown
    assert "Drill 1" in artifact.active_recall_markdown

    assert artifact.boundary_matrix_markdown is not None
    assert "Boundary Conditions" in artifact.boundary_matrix_markdown
    assert "Slutsky Symmetry" in artifact.boundary_matrix_markdown

    # OPML generation check
    assert artifact.opml_content is not None
    assert "<?xml version=" in artifact.opml_content
    assert '<opml version="2.0">' in artifact.opml_content
    assert '<outline text="Consumer Choice">' in artifact.opml_content
    assert '<outline text="Axioms of Preference">' in artifact.opml_content
    assert '<outline text="Completeness">' in artifact.opml_content

    # Validate XML parsing
    root = ET.fromstring(artifact.opml_content)
    assert root.tag == "opml"
    body = root.find("body")
    assert body is not None
    outlines = body.findall("outline")
    assert len(outlines) >= 1


def test_extract_artifacts_fallback_headings():
    legacy_markdown = """
# Macroeconomic Dynamics
## Real Business Cycle Theory
### Technology Shocks
- Exogenous TFP fluctuations drive output.
- Capital accumulation dynamics.
## New Keynesian Framework
### Nominal Rigidities
- Calvo staggered price setting.
    """.strip()

    adapter = StudySchemaExporterAdapter()
    artifact = adapter.extract_artifacts(legacy_markdown, "legacy_hash", "Macroeconomics")

    assert artifact.mindmap_mermaid is None
    assert artifact.flowchart_mermaid is None
    assert artifact.opml_content is not None

    # Should have parsed H1/H2/H3 into outlines
    assert '<outline text="Macroeconomic Dynamics">' in artifact.opml_content
    assert '<outline text="Real Business Cycle Theory">' in artifact.opml_content
    assert '<outline text="Technology Shocks">' in artifact.opml_content

    root = ET.fromstring(artifact.opml_content)
    assert root.tag == "opml"


def test_opml_xml_escaping():
    special_markdown = """
```mermaid
mindmap
  root((Models & Methods <2026> "Advanced"))
    Supply & Demand
```
    """.strip()

    adapter = StudySchemaExporterAdapter()
    artifact = adapter.extract_artifacts(special_markdown, "special_hash", "Special & Unique")

    assert "&amp;" in artifact.opml_content
    assert "&lt;" in artifact.opml_content
    assert "&gt;" in artifact.opml_content
    assert "&quot;" in artifact.opml_content

    # Must be valid XML
    root = ET.fromstring(artifact.opml_content)
    assert root.tag == "opml"
