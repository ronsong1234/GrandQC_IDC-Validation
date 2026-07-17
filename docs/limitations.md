# Limitations

Stated plainly, because the project is about reproducibility and honest reference handling.

1. **The matched SVS masks are a computational baseline, not biological ground truth.**
   Both arms run the *same* GrandQC, so the comparison certifies that IDC DICOM and the
   original SVS drive GrandQC to the same output. It says nothing about whether GrandQC's
   labels are *correct* — a shared model error is invisible to this test. Biological accuracy
   would require expert annotation or a separately validated manual reference.

2. **The Zenodo masks are not reproducible from the public GrandQC materials.** The authors'
   released 2024 code and weights reach only ~0.70 tissue IoU against the published masks on
   rim slides (Finding 3). Zenodo is therefore used only as a secondary provenance
   comparison, never as the primary correctness reference. The true reference-generation
   procedure remains unknown pending author confirmation
   (`provenance_experiment/AUTHORS_NOTE.md`).

3. **The TCGA-BRCA strata are confounded.** Codec, source-site, scanner, and magnification
   travel together: nearly all YBR_ICT slides are site AC (40×) or AO (20×), Zeiss slides are
   almost all plain JPEG, and 20× is dominated by a single site. A fully orthogonal
   codec × scanner × magnification design is not achievable from this collection. The
   stratified cohort shows equivalence *holds across* these strata; it does not isolate the
   effect of any single axis.

4. **This validates computational equivalence, not clinical accuracy.** The pipeline is
   suitable for QC of research-grade repositories; it is not a diagnostic device and has not
   been validated for clinical use.

5. **YBR_ICT prevalence is cohort-specific.** The 2.6 % figure is for TCGA-BRCA diagnostic
   H&E slides. Other IDC collections were converted at different times with different tools
   and may have entirely different codec/photometric distributions. Do not generalize the
   rate; re-measure per collection with `src/inspect_dicom_headers.py`.

6. **Scope of the equivalence numbers.** The headline 99.960 % / 99.988 % figures are from
   the 5-slide validated set. The 22-slide stratified run (`05_stratified_validation.ipynb`)
   is the intended confirmation at larger n; its results should be reported when complete.

7. **CPU vs GPU.** Validated numbers were produced on CPU (deterministic). GPU inference can
   introduce small numerical differences in principle; the equivalence claim is made for the
   CPU pipeline and should be re-confirmed if a GPU run is used as the reference.
