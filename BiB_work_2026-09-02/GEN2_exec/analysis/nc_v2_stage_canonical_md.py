from gate import gate, canary_gate, retry_limit
import pathlib

gate(__file__)

BASE = pathlib.Path(r"D:\Papers\Robin_Nature_2026\BiB_work_2026-09-02")
P1 = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.1_PlanA"
P2 = BASE / "STAR-Audit_NCOMMS_AgenticAI_投稿包_v2.3_Aligned"


def mini_task():
    assert (P1 / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.md").exists()
    return True


canary_gate(lambda: mini_task(), "Verify v2.1 SI template exists")


@retry_limit(2)
def main():
    (P2 / "03_Supplementary").mkdir(parents=True, exist_ok=True)
    (P2 / "05_Cover_Letter_and_Checklist").mkdir(parents=True, exist_ok=True)
    (P2 / "06_GitHub_Release_Synced").mkdir(parents=True, exist_ok=True)

    si = (P1 / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.md").read_text(encoding="utf-8")

    old_s1a = "**(A)** Verified on-topic grounded citation yield (%) across four progressive pipeline stages"
    new_s1a = (
        "**(A)** Grouped point-interval comparison (mean +/- binomial SE) of citation slot proportions across four pipeline metrics "
        "(`1. Ungated Ungrounded Error`, `2. Ungated Verified Yield`, `3. Module 3a Alone Parametric Yield`, and "
        "`4. Closed-Loop Module 3a + 3b Verified Yield`)"
    )
    assert old_s1a in si, "old_s1a not found"
    si = si.replace(old_s1a, new_s1a, 1)

    old_s2c = r"exact McNemar $p = 7.11 \times 10^{-15}$: +11 GLM-5.3"
    new_s2c = r"exact McNemar $p = 7.11 \times 10^{-15}$, error bars show paired McNemar 95% CIs: +11 GLM-5.3"
    assert old_s2c in si, "old_s2c not found"
    si = si.replace(old_s2c, new_s2c, 1)

    old_s3bc = (
        r"**(B)** Synthetic Monte Carlo parameter-recovery and confounded-null identifiability study ($M = 30$ candidates, $K = 300$ comparisons under strict $a < b$ index ordering; 400 simulations per cell). "
        r"Solid curves compare Bucket-3 Top-10 survival share under unadjusted BTL versus `OA-BTL` across true primacy $\gamma_{\text{true}} \in [0, 2.0]$; "
        r"dashed and dotted curves verify that when $\gamma_{\text{true}} = 0$ and Bucket 1 holds genuine biological superiority over Bucket 3 ($\Delta_{\text{B1-B3}} \in \{0, 0.5, 1.0, 1.5\}$), "
        r"`OA-BTL` tracks true merit share without false-positive primacy ($\hat{\gamma} \in [-0.003, +0.023]$) or artificial Bucket-3 promotion."
        "\n**(C)** Four-order hyperparameter sensitivity sweep"
    )
    new_s3bcd = (
        r"**(B)** Synthetic Monte Carlo parameter-recovery study ($M = 30$ candidates, $K = 300$ comparisons under strict $a < b$ index ordering; 400 simulations per cell), "
        r"comparing Bucket-3 Top-10 survival share under unadjusted BTL versus `OA-BTL` across true Slot-A primacy $\gamma_{\text{true}} \in [0, 2.0]$ against the 33.3% uniform benchmark."
        "\n"
        r"**(C)** Confounded-null Monte Carlo identifiability study ($\gamma_{\text{true}} = 0$, 400 simulations per cell) across genuine Bucket-1 biological superiority $\Delta_{\text{B1-B3}} \in \{0, 0.5, 1.0, 1.5\}$, "
        r"verifying that `OA-BTL` tracks true merit share without false-positive primacy ($\hat{\gamma} \in [-0.003, +0.023]$, 91.8% to 95.8% CI coverage) or artificial Bucket-3 promotion."
        "\n**(D)** Four-order hyperparameter sensitivity sweep"
    )
    assert old_s3bc in si, "old_s3bc not found"
    si = si.replace(old_s3bc, new_s3bcd, 1)
    si = si.replace("(Supplementary Fig. 3B)", "(Supplementary Fig. 3B, C)")

    (P2 / "03_Supplementary" / "Supplementary_Information_NC_v2.0_EN.md").write_text(si, encoding="utf-8")

    cl_en = (P1 / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_submission_EN.md").read_text(encoding="utf-8")
    cl_en = cl_en.replace("November 25, 2026", "November 26, 2026")
    (P2 / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_submission_EN.md").write_text(cl_en, encoding="utf-8")

    cl_zh = (P1 / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_CN_review.md").read_text(encoding="utf-8")
    cl_zh = cl_zh.replace("2026年11月25日", "2026年11月26日")
    (P2 / "05_Cover_Letter_and_Checklist" / "Cover_Letter_NCOMMS_AgenticAI_v2.0_CN_review.md").write_text(cl_zh, encoding="utf-8")

    chk = (P1 / "05_Cover_Letter_and_Checklist" / "NC_Reporting_Summary_Checklist_v2.0.md").read_text(encoding="utf-8")
    chk = chk.replace("_planA.py", "_canonical.py")
    (P2 / "05_Cover_Letter_and_Checklist" / "NC_Reporting_Summary_Checklist_v2.0.md").write_text(chk, encoding="utf-8")

    # Copy GitHub README into 06_GitHub_Release_Synced and update _planA.py -> _canonical.py
    gh_src = list((P1 / "06_GitHub_Release_Synced").glob("*.md"))
    for gf in gh_src:
        gtxt = gf.read_text(encoding="utf-8").replace("_planA.py", "_canonical.py").replace("v2.1 Plan-A", "v2.3 Aligned")
        (P2 / "06_GitHub_Release_Synced" / gf.name).write_text(gtxt, encoding="utf-8")

    print("STAGED ALL v2.3_Aligned MD TEMPLATES OK")


if __name__ == "__main__":
    main()
