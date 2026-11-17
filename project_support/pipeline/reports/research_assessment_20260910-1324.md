# Research Ledger Assessment

Historical duplicates are not independent runs.
Source analysis content and paired metric tables: research_inventory_20260910-1324.json.
Compromised M169/M172/M174 stopping evidence cannot establish convergence.

| ID | State | mIoU | Motivation contribution |
|----|-------|------|-------------------------|
| model_base1_quard2_c2f_enc_lite_posA_l1 | done_complete | 0.5012 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_posA | done_complete | 0.5009 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_l1 | done_complete | 0.5006 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_nomask | done_complete | 0.4997 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite | done_complete | 0.4992 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_l3 | done_complete | 0.4981 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_noroute | done_complete | 0.4972 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_langc2f_scale_l1 | done_complete | 0.4967 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_cag | done_complete | 0.4962 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_adaptive_l1 | done_complete | 0.4961 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_langroute_l1 | done_complete | 0.4956 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_posB | done_complete | 0.4953 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_balanced_l1 | done_complete | 0.4952 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_posC | done_complete | 0.4952 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_langc2f_l1 | done_complete | 0.4950 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_init0 | done_complete | 0.4949 | Context candidate above baseline, no champion improvement |
| model_base1_gbcr_local_l1 | done_complete | 0.4943 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_l4 | done_complete | 0.4931 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_posA_l1_layerscale | done_complete | 0.4921 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_cfe | done_complete | 0.4901 | Context candidate above baseline, no champion improvement |
| model_base1 | done_complete | 0.4894 | No observed baseline improvement |
| model_base1_quard2_c2f_enc | done_complete | 0.4891 | No observed baseline improvement |
| model_base1_quard2_c2f_pq | done_complete | 0.4864 | No observed baseline improvement |
| model_base1_gbcr_pointgate_l1 | done_complete | 0.4841 | No observed baseline improvement |
| model_base1_quard2_c2f_enc_lite_posA_l1_noroute | done_complete | 0.4800 | No observed baseline improvement |
| model_base1_topk_c2f_bottleneck_l1 | done_complete | 0.4794 | No observed baseline improvement |
| model_base1_cluster_fixed_ctx_l1_ls | done_complete | 0.4790 | No observed baseline improvement |
| model_base1_cluster_fixed_ctx_l1 | done_complete | 0.4760 | No observed baseline improvement |
| model_base1_quard2_c2f_enc_lite_attnpool | done_complete | 0.4711 | No observed baseline improvement |
| model_base2_quard2_c2f | done_complete | 0.4690 | No observed baseline improvement |
| model_base1_quard2_c2f_enc_lite_posenc | done_complete | 0.4689 | No observed baseline improvement |
| model_base2_quard2_c2f_enc | done_complete | 0.4664 | No observed baseline improvement |
| model_base2_quard2_l1 | done_complete | 0.4655 | No observed baseline improvement |
| model_base2_quard2_c2f_enc_gm1 | done_complete | 0.4652 | No observed baseline improvement |
| model_base2_quard2_c2f_pq | done_complete | 0.4646 | No observed baseline improvement |
| model_base2 | done_complete | 0.4641 | No observed baseline improvement |
| model_base2_quard2_nomask | done_complete | 0.4633 | No observed baseline improvement |
| model_base2_quard2 | done_complete | 0.4598 | No observed baseline improvement |
| model_base1_quard2_c2f_enc_lite_posA_l1_true_route | done_complete | 0.4468 | No observed baseline improvement |
| model_base1_cluster_hier_add_l1 | done_complete | 0.4041 | No observed baseline improvement |
| model_base1_cluster_hier_content_l1 | done_complete | 0.3659 | No observed baseline improvement |
| C1-layerscale | stopped_unknown | 0.4998 | Context candidate above baseline, no champion improvement; compromised termination |
| D1-detail | done_earlystop | 0.4979 | Context candidate above baseline, no champion improvement |
| D1-detail | stopped_unknown | 0.5003 | Context candidate above baseline, no champion improvement; compromised termination |
| E4-res_detail | stopped_unknown | 0.4944 | Context candidate above baseline, no champion improvement; compromised termination |
| A4-shuffle | done_earlystop | 0.4941 | Context candidate above baseline, no champion improvement |
| M1-QGC | done_earlystop | 0.4939 | Context candidate above baseline, no champion improvement |
| M6-QSF | stopped_unknown | 0.4866 | No observed baseline improvement; compromised termination |
| M17-ORT | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M16-CSR | done_earlystop | 0.4875 | No observed baseline improvement |
| M18-S2FM | done_earlystop | 0.4933 | Context candidate above baseline, no champion improvement |
| M19-S2FC | stopped_unknown | 0.4944 | Context candidate above baseline, no champion improvement; compromised termination |
| M17-ORT | done_earlystop | 0.5005 | Context candidate above baseline, no champion improvement |
| M20-DET | stopped_unknown | 0.4955 | Context candidate above baseline, no champion improvement; compromised termination |
| M22-XCA | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M22-XCA | done_earlystop | 0.4954 | Context candidate above baseline, no champion improvement |
| M21-HYB | stopped_unknown | 0.4898 | Context candidate above baseline, no champion improvement; compromised termination |
| M23-CMX | stopped_unknown | 0.4910 | Context candidate above baseline, no champion improvement; compromised termination |
| M24-ORT-D | done_earlystop | 0.4955 | Context candidate above baseline, no champion improvement |
| M25-REF | stopped_unknown | 0.4892 | No observed baseline improvement; compromised termination |
| M26-ORT-HYB | stopped_unknown | 0.4998 | Context candidate above baseline, no champion improvement; compromised termination |
| M27-ORT-W5 | stopped_unknown | 0.4959 | Context candidate above baseline, no champion improvement; compromised termination |
| M28-ORT-W1 | stopped_unknown | 0.3916 | No observed baseline improvement; compromised termination |
| M33-DTW | stopped_unknown | 0.4968 | Context candidate above baseline, no champion improvement; compromised termination |
| M32-DRP | stopped_unknown | 0.5012 | Context candidate above baseline, no champion improvement; compromised termination |
| M34-Q2P | stopped_unknown | 0.4904 | Context candidate above baseline, no champion improvement; compromised termination |
| M38-FLM | stopped_unknown | 0.4865 | No observed baseline improvement; compromised termination |
| M39-C2C | done_earlystop | 0.4865 | No observed baseline improvement |
| M41-CTF | done_earlystop | 0.4995 | Context candidate above baseline, no champion improvement |
| M40-SWI | stopped_unknown | 0.4970 | Context candidate above baseline, no champion improvement; compromised termination |
| M42-WCA | done_earlystop | 0.4890 | No observed baseline improvement |
| M43-CLN | stopped_unknown | 0.4930 | Context candidate above baseline, no champion improvement; compromised termination |
| M45-NCR | stopped_unknown | 0.4980 | Context candidate above baseline, no champion improvement; compromised termination |
| M46-SHC | stopped_unknown | 0.4946 | Context candidate above baseline, no champion improvement; compromised termination |
| M44-CSF | done_earlystop | 0.4958 | Context candidate above baseline, no champion improvement |
| M47-FILM | done_earlystop | 0.4936 | Context candidate above baseline, no champion improvement |
| M48-BIL | done_earlystop | 0.4919 | Context candidate above baseline, no champion improvement |
| M49-NLR | done_earlystop | 0.4948 | Context candidate above baseline, no champion improvement |
| M56-DOT | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M57-DET-ORT | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M50-DGC | stopped_unknown | 0.4913 | Context candidate above baseline, no champion improvement; compromised termination |
| M51-DCA | done_earlystop | 0.4893 | No observed baseline improvement |
| M55-SCF | done_earlystop | 0.4927 | Context candidate above baseline, no champion improvement |
| M59-DET-QSF | stopped_unknown | 0.4961 | Context candidate above baseline, no champion improvement; compromised termination |
| M60-DET-CSF | done_earlystop | 0.4973 | Context candidate above baseline, no champion improvement |
| M61-SCT | done_earlystop | 0.4854 | No observed baseline improvement |
| M62-ORTG | done_earlystop | 0.4979 | Context candidate above baseline, no champion improvement |
| M63-PSR | done_earlystop | 0.4964 | Context candidate above baseline, no champion improvement |
| M64-SSP | done_earlystop | 0.4928 | Context candidate above baseline, no champion improvement |
| M54-SAC | done_earlystop | 0.4892 | No observed baseline improvement |
| M53-VAC | stopped_unknown | 0.4889 | No observed baseline improvement; compromised termination |
| M52-CCR | stopped_unknown | 0.4948 | Context candidate above baseline, no champion improvement; compromised termination |
| M66-DET-HCG | stopped_unknown | 0.4955 | Context candidate above baseline, no champion improvement; compromised termination |
| M69-ITER | done_earlystop | 0.4978 | Context candidate above baseline, no champion improvement |
| M71-CCP | done_earlystop | 0.4934 | Context candidate above baseline, no champion improvement |
| M58-DET-DRP | done_earlystop | 0.498 | Context candidate above baseline, no champion improvement |
| M67-PSR-HCG | done_earlystop | 0.496 | Context candidate above baseline, no champion improvement |
| M68-SSP-HCG | done_earlystop | 0.4965 | Context candidate above baseline, no champion improvement |
| M73-CCP-DET | done_earlystop | 0.4952 | Context candidate above baseline, no champion improvement |
| M81-CTF-HCG | waiting |  | No usable efficacy metric |
| M82-DET-CTF | waiting |  | No usable efficacy metric |
| M83-DET-REAG-CASC | waiting |  | No usable efficacy metric |
| M84-DET-CTF-HCG | waiting |  | No usable efficacy metric |
| M74-CCP-HCG-DET | done_earlystop | 0.4948 | Context candidate above baseline, no champion improvement |
| M78-REAGG-HCG | done_earlystop | 0.5008 | Context candidate above baseline, no champion improvement |
| M80-REAG-CASC-HCG | stopped_unknown | 0.4965 | Context candidate above baseline, no champion improvement; compromised termination |
| M81-CTF-HCG | stopped_unknown | 0.5012 | Context candidate above baseline, no champion improvement; compromised termination |
| M82-DET-CTF | stopped_unknown | 0.4989 | Context candidate above baseline, no champion improvement; compromised termination |
| M83-DET-REAG-CASC | stopped_unknown | 0.3018 | No observed baseline improvement; compromised termination |
| M75-DET-ITER | stopped_unknown | 0.4956 | Context candidate above baseline, no champion improvement; compromised termination |
| M76-DET-REAGG | stopped_unknown | 0.4909 | Context candidate above baseline, no champion improvement; compromised termination |
| M77-ITER-HCG | stopped_unknown | 0.4933 | Context candidate above baseline, no champion improvement; compromised termination |
| M82-DET-CTF | stopped_unknown | 0.4989 | Context candidate above baseline, no champion improvement; compromised termination |
| M83-DET-REAG-CASC | done_earlystop | 0.4910 | Context candidate above baseline, no champion improvement |
| M84-DET-CTF-HCG | done_earlystop | 0.4990 | Context candidate above baseline, no champion improvement |
| M85-QMOD | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M88-QMOD-MLAY | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M81-CONS | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M87-DET-CONS | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M90-CTF-HCG-S3 | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M91-HCG-R2 | done_earlystop | 0.4960 | Context candidate above baseline, no champion improvement |
| M93-CTF-SEF | done_earlystop | 0.4910 | Context candidate above baseline, no champion improvement |
| model_base1_quard2_c2f_enc_lite_posA_l1_ctf_sef | done_earlystop | 0.4910 | Context candidate above baseline, no champion improvement |
| M92-CTF-HCG-ORT | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M94-HCG-ORT | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M89-CTF-HCG-R2 | done_earlystop | 0.4980 | Context candidate above baseline, no champion improvement |
| M95-CTF-HCG-CSORT | done_earlystop | 0.5020 | Champion reference; robustness unproven |
| M96-CTF-HCG-2LAY | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M99-CHAMP-S42 | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M100-CHAMP-S123 | done_earlystop | 0.4980 | Context candidate above baseline, no champion improvement |
| M102-CTF-HCG-S2026 | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M101-CHAMP-S2026 | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M103-CTF-HCG-CSORT-S2026 | stopped_unknown | 0.4902 | Context candidate above baseline, no champion improvement; compromised termination |
| M98-CHAMP-CSORT | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M104-CTF-HCG-CSORT-S42 | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M105-CTF-HCG-CSORT-S123 | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M106-CHAMP-CSORT-S42 | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M107-CHAMP-CSORT-S123 | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M108-CHAMP-CSORT-S2026 | stopped_unknown | ? | No usable efficacy metric; compromised termination |
| M109-CSORT-MSG | done_earlystop | 0.5010 | Context candidate above baseline, no champion improvement |
| M110-CTF-HCG-MEMBANK | waiting |  | No usable efficacy metric |
| M111-CTF-HCG-SRL | waiting |  | No usable efficacy metric |
| M98-CHAMP-CSORT | crashed | N/A | No usable efficacy metric; compromised termination |
| M106-CHAMP-CSORT-S42 | crashed | N/A | No usable efficacy metric; compromised termination |
| M107-CHAMP-CSORT-S123 | crashed | N/A | No usable efficacy metric; compromised termination |
| M108-CHAMP-CSORT-S2026 | crashed | N/A | No usable efficacy metric; compromised termination |
| M110-CTF-HCG-MEMBANK | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M118-CTF-HCG-LCC | waiting |  | No usable efficacy metric |
| M97-CHAMP-ORT | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M111-CTF-HCG-SRL | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M112-MEMBANK-S42 | done_earlystop | 0.4890 | No observed baseline improvement |
| M112-MEMBANK-S42 | done_earlystop | 0.4890 | No observed baseline improvement |
| M86-MLAY | done_earlystop | 0.5010 | Context candidate above baseline, no champion improvement |
| M122-MLAY-S123 | waiting |  | No usable efficacy metric |
| M114-MEMBANK-S123 | done_earlystop | 0.5010 | Context candidate above baseline, no champion improvement |
| M113-SRL-S42 | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M115-CTF-HCG-CCL | done_earlystop | 0.4890 | No observed baseline improvement |
| M117-CTF-HCG-BCF | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M116-CTF-HCG-CGA | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M127-DET-DCA | waiting |  | No usable efficacy metric |
| M128-DET-DCM | waiting |  | No usable efficacy metric |
| M118-CTF-HCG-LCC | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M119-CTF-HCG-MFP | done_earlystop | 0.5020 | Champion reference; robustness unproven |
| M123-CTF-HCG-DCA | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M124-CTF-HCG-DCM | done_earlystop | 0.5010 | Context candidate above baseline, no champion improvement |
| M127-DET-DCA | done_earlystop | 0.4870 | No observed baseline improvement |
| M128-DET-DCM | done_earlystop | 0.4990 | Context candidate above baseline, no champion improvement |
| M129-MFP-S42 | done_earlystop | 0.4870 | No observed baseline improvement |
| M130-MFP-S123 | done_earlystop | 0.4960 | Context candidate above baseline, no champion improvement |
| M133-DCMV | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M126-MLAY-DCM | done_earlystop | 0.4980 | Context candidate above baseline, no champion improvement |
| M125-MLAY-DCA | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M134-DUAL | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M135-DCM-S42 | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M136-MLAY-DCMV | done_earlystop | 0.4960 | Context candidate above baseline, no champion improvement |
| M137-DCMV-S42 | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M138-MLAY-DUAL | done_earlystop | 0.4990 | Context candidate above baseline, no champion improvement |
| M140-CTF-HCG-CLICA | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M139-MLAY-DUAL-LEGACY | done_earlystop | 0.4880 | No observed baseline improvement |
| M141-CTF-HCG-CSIC | done_earlystop | 0.4960 | Context candidate above baseline, no champion improvement |
| M121-CTF-HCG-MLAY-DET | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M142-CTF-HCG-CLICA-CSIC | done_earlystop | 0.4890 | No observed baseline improvement |
| M143-CTF-HCG-OBJG | done_earlystop | 0.5000 | Context candidate above baseline, no champion improvement |
| M144-CTF-HCG-LQA | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M145-CTF-HCG-CSORT-ALL | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M146-CTF-HCG-CSORT-DET | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M148-CTF-HCG-CSORT-DCM | done_earlystop | 0.4990 | Context candidate above baseline, no champion improvement |
| M147-MLAY-CSORT | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M120-CTF-HCG-MLAY-S42 | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M149-CTF-HCG-CSORT-SG | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M150-CTF-HCG-CSORT-OWC | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M151-CTF-HCG-CSORT-ODW | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M152-CTF-HCG-CSORT-F1 | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M153-CTF-HCG-CSORT-MFP | done_earlystop | 0.5000 | Context candidate above baseline, no champion improvement |
| M156-CTF-HCG-CSORT-CP | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M154-CTF-HCG-CSORT-GSC | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M157-CTF-HCG-CSORT-PMD | done_earlystop | 0.4990 | Context candidate above baseline, no champion improvement |
| M155-CTF-HCG-CSORT-RF | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M159-CTF-HCG-CSORT-GEO | done_earlystop | 0.4840 | No observed baseline improvement |
| M158-CTF-HCG-CSORT-PMD-SH | done_earlystop | 0.4950 | Context candidate above baseline, no champion improvement |
| M161-CTF-HCG-CSORT-MQF | done_earlystop | 0.4920 | Context candidate above baseline, no champion improvement |
| M162-CTF-HCG-CSORT-MQF-SH | done_earlystop | 0.4980 | Context candidate above baseline, no champion improvement |
| M122-MLAY-S123 | done_earlystop | 0.4940 | Context candidate above baseline, no champion improvement |
| M163-CTF-HCG-CSORT-MQC | done_earlystop | 0.4899 | Context candidate above baseline, no champion improvement |
| M166-CTF-HCG-CSORT-MPF | done_earlystop | 0.4899 | Context candidate above baseline, no champion improvement |
| M160-CTF-HCG-CSORT-GEO-SH | done_earlystop | 0.4910 | Context candidate above baseline, no champion improvement |
| M167-CTF-HCG-CSORT-MQX | done_earlystop | 0.4910 | Context candidate above baseline, no champion improvement |
| M168-CTF-HCG-CSORT-MQD | done_earlystop | 0.4900 | Context candidate above baseline, no champion improvement |
| M170-CTF-HCG-CSORT-MQR | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement |
| M169-CTF-HCG-CSORT-MQB | done_earlystop | 0.5000 | Context candidate above baseline, no champion improvement; compromised termination |
| M172-CTF-HCG-CSORT-MQS | done_earlystop | 0.4970 | Context candidate above baseline, no champion improvement; compromised termination |
| M171-CTF-HCG-CSORT-MQCC | stopped_unknown | 0.4936 | Context candidate above baseline, no champion improvement; compromised termination |
| M173-CTF-HCG-CSORT-MQCI | stopped_unknown | 0.4921 | Context candidate above baseline, no champion improvement; compromised termination |
| M164-CTF-HCG-CSORT-MQU | stopped_unknown | 0.4950 | Context candidate above baseline, no champion improvement; compromised termination |
| M165-CTF-HCG-CSORT-MQH | stopped_unknown | 0.4911 | Context candidate above baseline, no champion improvement; compromised termination |
| M174-CTF-HCG-CSORT-MQHC | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement; compromised termination |
| M177-CTF-HCG-CSORT-MQBC | done_earlystop | 0.4963 | Context candidate above baseline, no champion improvement |
| M176-CTF-HCG-CSORT-MQSD | done_earlystop | 0.4936 | Context candidate above baseline, no champion improvement |
| M178-CTF-HCG-CSORT-MQTD | done_earlystop | 0.4930 | Context candidate above baseline, no champion improvement |
| M175-CTF-HCG-CSORT-MQHF | done_earlystop | 0.4968 | Context candidate above baseline, no champion improvement |
| M183-CTF-HCG-CSORT-HQI | done_earlystop | 0.4915 | Context candidate above baseline, no champion improvement |
