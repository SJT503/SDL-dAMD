#!/usr/bin/env python3
"""
Upgrade Ref [50] (Saul et al. 2022 Nat Commun SenMayo, PMID:35974106),
Ref [53] (Minikel et al. 2024 Nature human-genetic target validation, PMID:38632401),
and pinpoint [58, 59, 60] dAMD pathway placements across all manuscript editions.
"""

from pathlib import Path

BASE = Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")

OLD_REF_50 = "50. Chen H, Lee YJ, Ovando-Ricardez JA, Rosas L, Rojas M, Mora AL, et al. Recovering single-cell expression profiles from spatial transcriptomics with scResolve. *Cell Rep Methods* 4, 100864 (2024). DOI:10.1016/j.crmeth.2024.100864. PMID:39326411"
NEW_REF_50 = "50. Saul D, Kosinsky RL, Atkinson EJ, Doolittle ML, Zhang X, LeBrasseur NK, et al. A new gene set identifies senescent cells and predicts senescence-associated pathways across tissues. *Nat Commun* 13, 4827 (2022). DOI:10.1038/s41467-022-32552-1. PMID:35974106"

OLD_REF_53 = "53. Cardoen B, Ben Yedder H, Nabi IR, Hamarneh G. Closing the multichannel gap through computational reconstruction of interaction in super-resolution microscopy. *Patterns* 6, 101181 (2025). DOI:10.1016/j.patter.2025.101181. PMID:40486966"
NEW_REF_53 = "53. Minikel EV, Painter JL, Dong CC, Nelson MR. Refining the impact of genetic evidence on clinical success. *Nature* 629, 624-629 (2024). DOI:10.1038/s41586-024-07316-0. PMID:38632401"


def patch_file(p: Path, extra_subs: list[tuple[str, str]]) -> None:
    t = p.read_text(encoding="utf-8")
    assert OLD_REF_50 in t or "build_nmi_primary_edition" in p.name, f"Missing OLD_REF_50 in {p.name}"
    assert OLD_REF_53 in t or "build_nmi_primary_edition" in p.name, f"Missing OLD_REF_53 in {p.name}"
    t = t.replace(OLD_REF_50, NEW_REF_50).replace(OLD_REF_53, NEW_REF_53)
    for a, b in extra_subs:
        assert a in t, f"Target not found in {p.name}: {a[:80]}"
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8")
    print(f"[OK] Patched {p.name}")


def main() -> None:
    npj_en_subs = [
        (
            "distinct transcriptomic senescence signatures (such as primary `SenMayo` versus secondary senescence modules sharing $<1\\%$ exact gene overlap yet correlating at $r = 0.89$, alongside spatial convergence across `SenMayo`, `Fridman`, and `CellAge`) capture the same underlying cellular state [50].",
            "distinct transcriptomic senescence signatures (`SenMayo`, `Fridman`, and `CellAge`) exhibit minimal single-gene overlap while capturing the same underlying cellular state [50].",
        ),
        (
            "Following computational validation benchmarks that anchor algorithmic corrections against orthogonal human genetics, animal models, and clinical trials [20, 53],",
            "Following target-validation benchmarks showing that orthogonal human genetic, animal-model, and clinical-trial evidence anchors causal biological truth [53],",
        ),
        (
            "mathematical interaction benchmarks [53],",
            "human-genetic target-validation benchmarks [53],",
        ),
        (
            "Following reproducibility and transparency standards for computational methodology benchmarks [20, 27, 53],",
            "Following reproducibility and transparency standards for computational methodology benchmarks [20, 27],",
        ),
    ]
    patch_file(BASE / "MANUSCRIPT_NPJ_DigitalMed_Backup_v1.0.md", npj_en_subs)
    patch_file(BASE / "MANUSCRIPT_GEN2_NaturePortfolio_v1.0.md", npj_en_subs)

    npj_zh_subs = [
        ("（如初级 `SenMayo` 与次级衰老模块精确基因重叠 $<1\\%$ 但相关性达 $r = 0.89$，且与 `Fridman`、`CellAge` 空间共定位）实则捕获同一细胞状态 [50]", "（如 `SenMayo`、`Fridman` 与 `CellAge`）虽单基因重叠极低却捕获同一细胞衰老状态 [50]"),
        ("[20, 53]", "[53]"),
        ("[20, 27, 53]", "[20, 27]"),
    ]
    # Inspect exact Chinese strings in STAR-Audit_npj备选版_手稿全文中文版_审核稿.md safely
    zh_p = BASE / "STAR-Audit_npj备选版_手稿全文中文版_审核稿.md"
    zt = zh_p.read_text(encoding="utf-8").replace(OLD_REF_50, NEW_REF_50).replace(OLD_REF_53, NEW_REF_53)
    zt = zt.replace("[20, 53]", "[53]").replace("[20, 27, 53]", "[20, 27]")
    zt = zt.replace("数学互作基准 [53]", "人类遗传学靶点验证基准 [53]")
    zh_p.write_text(zt, encoding="utf-8")
    print(f"[OK] Patched {zh_p.name}")

    # Patch Patterns backup
    pat_p = BASE / "MANUSCRIPT_GEN2_v1.0.md"
    pt = pat_p.read_text(encoding="utf-8").replace(OLD_REF_50, NEW_REF_50).replace(OLD_REF_53, NEW_REF_53)
    pt = pt.replace("[20, 53]", "[53]").replace("[20, 27, 53]", "[20, 27]")
    pat_p.write_text(pt, encoding="utf-8")
    print(f"[OK] Patched {pat_p.name}")

    # Patch build_nmi_primary_edition.py for NMI EN & ZH
    b_p = BASE / "GEN2_exec" / "analysis" / "build_nmi_primary_edition.py"
    bt = b_p.read_text(encoding="utf-8")
    en_targets = [
        (
            "distinct transcriptomic senescence modules (`SenMayo`, `Fridman`, `CellAge`) share $<1\\\\%$ gene overlap while capturing identical cellular states [50]",
            "distinct transcriptomic senescence modules (`SenMayo`, `Fridman`, `CellAge`) exhibit minimal single-gene overlap while capturing shared cellular states [50]",
        ),
        (
            "Anchoring rescued candidates against orthogonal genetic, animal-model, and clinical-trial truth [20, 53]",
            "Anchoring rescued candidates against orthogonal human-genetic, animal-model, and clinical-trial truth [53]",
        ),
        (
            "In dAMD, `OA-BTL` rescued `GAS6/PROS1–MERTK` RPE efferocytosis (`Rank 11 -> 7` [39, 54–57]), `TIMP3/MMP2/MMP9` matrix turnover (`Rank 15 -> 8`), `ABCA1/LIPC/CETP` cholesterol efflux (`Rank 15 -> 6`), `CD59` membrane-attack-complex inhibition (`Rank 11 -> 5` [37, 40, 58–60]), and `MTTP/APOB100` lipoprotein drusen biogenesis (`Rank 12 -> 6` [42, 61]).",
            "In dAMD, `OA-BTL` rescued `GAS6/PROS1–MERTK` RPE efferocytosis (`Rank 11 -> 7` [39, 54–57]), `TIMP3/MMP2/MMP9` matrix turnover (`Rank 15 -> 8` [37, 58, 59]), `ABCA1/LIPC/CETP` cholesterol efflux (`Rank 15 -> 6` [37, 58]), `CD59` membrane-attack-complex inhibition (`Rank 11 -> 5` [40, 60]), and `MTTP/APOB100` lipoprotein drusen biogenesis (`Rank 12 -> 6` [42, 61]).",
        ),
    ]
    for a, b in en_targets:
        assert a in bt, f"Missing target in build_nmi_primary_edition.py: {a[:90]}"
        bt = bt.replace(a, b)
    # Also update Chinese NMI core inside build_nmi_primary_edition.py
    bt = bt.replace("精确基因重叠 $<1\\\\%$ 却捕获同一细胞状态 [50]", "单基因重叠极低却捕获同一细胞衰老状态 [50]")
    bt = bt.replace("共享 $<1\\\\%$ 基因重叠却捕获同一细胞状态 [50]", "单基因重叠极低却捕获同一细胞衰老状态 [50]")
    bt = bt.replace("[20, 53]", "[53]")
    bt = bt.replace(
        "`TIMP3/MMP2/MMP9` 基质周转（`第 15 -> 8 名`）、`ABCA1/LIPC/CETP` 胆固醇外流（`第 15 -> 6 名`）、`CD59` 膜攻击复合物抑制（`第 11 -> 5 名` [37, 40, 58–60]）",
        "`TIMP3/MMP2/MMP9` 基质周转（`第 15 -> 8 名` [37, 58, 59]）、`ABCA1/LIPC/CETP` 胆固醇外流（`第 15 -> 6 名` [37, 58]）、`CD59` 膜攻击复合物抑制（`第 11 -> 5 名` [40, 60]）",
    )
    b_p.write_text(bt, encoding="utf-8")
    print(f"[OK] Patched {b_p.name}")


if __name__ == "__main__":
    main()
