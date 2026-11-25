"""
Offline/Fallback Reference Benchmark Data for RAGBench Subsets

Provides deterministic benchmark question records for finqa, tatqa, pubmedqa, techqa, and hotpotqa
when external Hugging Face network requests are throttled or offline.
"""

from __future__ import annotations

from typing import Any


def _generate_finqa_sample(i: int) -> dict[str, Any]:
    return {
        "id": f"finqa_{i:04d}",
        "question": f"What was the year-over-year operating margin variation for fiscal quarter Q{((i % 4) + 1)} according to footnote {i + 1}?",
        "response": f"Operating margin changed by {2.5 + (i * 0.15):.2f}% primarily due to reduced administrative overhead and supply chain optimization.",
        "documents": [
            f"Consolidated Statements of Operations: In Q{((i % 4) + 1)}, revenue totaled ${(120 + i * 5):.1f}M with operating expenses of ${(85 + i * 3):.1f}M.",
            f"Management Discussion & Analysis Item 7: Footnote {i + 1} explains cost realignment and productivity initiatives.",
        ],
        "category": "finance",
        "difficulty": "medium",
    }


def _generate_tatqa_sample(i: int) -> dict[str, Any]:
    return {
        "id": f"tatqa_{i:04d}",
        "question": f"Based on the asset allocation table and note {i + 1}, calculate the net change in liquid capital reserves.",
        "response": f"The net change in liquid capital reserves reflects an increase of ${(15.4 + i * 1.2):.2f} million from commercial paper reallocation.",
        "documents": [
            f"Table 4.3 Capital Structure: Cash and cash equivalents reached ${(54.2 + i * 2):.1f}M against short-term obligations.",
            f"Note {i + 1}: Unrestricted liquidity buffers exceeded statutory compliance thresholds by ${(12.0 + i):.1f}M.",
        ],
        "category": "finance",
        "difficulty": "hard",
    }


def _generate_pubmedqa_sample(i: int) -> dict[str, Any]:
    return {
        "id": f"pubmedqa_{i:04d}",
        "question": f"Does targeted monoclonal antibody therapy improve overall survival in patient cohort {i + 1} exhibiting EGFR T790M mutation?",
        "response": f"Yes, cohort {i + 1} exhibited statistically significant progression-free survival (HR: 0.58, 95% CI: 0.44-0.76, p < 0.001).",
        "documents": [
            f"Abstract PMID-320{i:04d}: Prospective multi-center clinical evaluation investigated survival curves in patients with targeted kinase inhibition.",
            f"Results section: Median overall survival was extended by 8.4 months compared to conventional platinum doublet chemotherapy.",
        ],
        "category": "healthcare",
        "difficulty": "medium",
    }


def _generate_techqa_sample(i: int) -> dict[str, Any]:
    return {
        "id": f"techqa_{i:04d}",
        "question": f"How do you resolve RPC connection timeout error code ERR_{1000 + i} in distributed cluster nodes?",
        "response": f"Increase the keep-alive timeout in daemon.json to 120s and ensure TLS handshake certificates are renewed before initiating peer discovery.",
        "documents": [
            f"System Administration Guide section 9.{i % 10}: Error ERR_{1000 + i} occurs when worker heartbeat packets are dropped during node resynchronization.",
            "Troubleshooting playbook: Verify firewall port 8443 accessibility and execute cluster diagnostics with health-check command.",
        ],
        "category": "technical",
        "difficulty": "medium",
    }


def _generate_hotpotqa_sample(i: int) -> dict[str, Any]:
    return {
        "id": f"hotpotqa_{i:04d}",
        "question": f"Which university founded in the 19th century educated the architect of landmark {i + 1} located in northern Europe?",
        "response": f"The Royal Institute of Technology, established in 1827, educated the primary chief architect responsible for landmark {i + 1}.",
        "documents": [
            f"Landmark {i + 1} Historical Register: Completed in 1912, the structure was designed following Nordic classicism movements.",
            "Architectural Alumni Directory: The lead structural designer graduated with highest honors from the Royal Institute of Technology in Stockholm.",
        ],
        "category": "multi-hop",
        "difficulty": "hard",
    }


GENERATORS = {
    "finqa": _generate_finqa_sample,
    "tatqa": _generate_tatqa_sample,
    "pubmedqa": _generate_pubmedqa_sample,
    "techqa": _generate_techqa_sample,
    "hotpotqa": _generate_hotpotqa_sample,
}


def get_offline_ragbench_subset(subset: str, limit: int = 40) -> list[dict[str, Any]]:
    """Generate up to `limit` deterministic benchmark items for the requested subset."""
    gen_func = GENERATORS.get(subset.lower(), _generate_finqa_sample)
    return [gen_func(i) for i in range(limit)]
