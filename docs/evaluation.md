# ReadBack: Evaluation Framework & Mathematical Metrics

## 1. Evaluation Methodology
To assess AI fidelity in medical document explanation, we compare two paradigms across an evaluation dataset of 100+ synthetic documents:

1. **Baseline System**:
   $$\text{Document} \xrightarrow{\text{Direct Prompting}} \text{LLM Explanation}$$
   *No structured schema, no independent extraction, no fidelity gating.*

2. **ReadBack System**:
   $$\text{Document} \to \text{Structured Extraction} \to \text{User Confirmation} \to \text{LLM Explanation} \to \text{Independent Re-Extraction} \to \text{Field-by-Field Verification} \to \text{Gate}$$

---

## 2. Mathematical Definition of Metrics

### 2.1 Document Fidelity Score (DFS)
Measures the proportion of confirmed facts faithfully preserved in the explanation:
$$\text{DFS} = \left( \frac{\sum_{i=1}^{N_{\text{fields}}} \mathbb{I}(\text{Field}_i \text{ is exact match})}{N_{\text{fields}}} \right) \times 100\%$$
*Where $\mathbb{I}(\cdot)$ is the indicator function evaluating normalized numeric, unit, medication, and negation match.*

### 2.2 Numeric Error Rate (NER)
Proportion of numeric medical values that differ between the original document and the explanation:
$$\text{NER} = \frac{\sum \mathbb{I}(|v_{\text{original}} - v_{\text{explanation}}| > \epsilon)}{N_{\text{numeric fields}}}$$

### 2.3 Unit Error Rate (UER)
Proportion of measurements where the unit was omitted or replaced with an incorrect unit (e.g., $g/dL \to mg/dL$):
$$\text{UER} = \frac{\sum \mathbb{I}(\text{Unit}_{\text{norm}}(\text{original}) \neq \text{Unit}_{\text{norm}}(\text{explanation}))}{N_{\text{units}}}$$

### 2.4 Drug Name Corruption Rate (DCR)
Rate at which medication names are altered to different chemical or brand names:
$$\text{DCR} = \frac{\sum \mathbb{I}(\text{Drug}_{\text{original}} \neq \text{Drug}_{\text{explanation}})}{N_{\text{medications}}}$$

### 2.5 Dosage Error Rate (DER)
Rate at which prescribed strength or quantity is modified (e.g., $500\text{ mg} \to 1000\text{ mg}$):
$$\text{DER} = \frac{\sum \mathbb{I}(\text{Dose}_{\text{original}} \neq \text{Dose}_{\text{explanation}})}{N_{\text{dosages}}}$$

### 2.6 Frequency Error Rate (FER)
Rate of frequency mutations (e.g., twice daily $\to$ once daily):
$$\text{FER} = \frac{\sum \mathbb{I}(\text{Freq}_{\text{original}} \neq \text{Freq}_{\text{explanation}})}{N_{\text{frequencies}}}$$

### 2.7 Negation Flip Rate (NFR)
Rate at which clinical prohibitions or restrictions are inverted (e.g., "Do NOT take on empty stomach" $\to$ "Take on empty stomach"):
$$\text{NFR} = \frac{\sum \mathbb{I}(\text{Negation}_{\text{original}} \neq \text{Negation}_{\text{explanation}})}{N_{\text{instructions}}}$$

### 2.8 Omitted Abnormal Flag Rate (OFR)
Rate at which critical laboratory flags (`LOW`, `HIGH`, `CRITICAL`) are dropped or reported as `NORMAL`:
$$\text{OFR} = \frac{\sum \mathbb{I}(\text{Flag}_{\text{orig}} \in \{\text{LOW}, \text{HIGH}\} \land \text{Flag}_{\text{expl}} = \text{NORMAL})}{N_{\text{abnormal flags}}}$$

### 2.9 Verifier Catch Rate (VCR)
Sensitivity of ReadBack in detecting and blocking corrupted explanations:
$$\text{VCR} = \frac{\text{True Blocks (Corrupted explanations blocked)}}{\text{Total Corrupted Explanations}} \times 100\%$$

### 2.10 False Block Rate (FBR)
Specificity penalty—faithful explanations incorrectly rejected by the verification engine:
$$\text{FBR} = \frac{\text{False Blocks (Faithful explanations blocked)}}{\text{Total Faithful Explanations}} \times 100\%$$

---

## 3. Synthetic Benchmark Dataset
The evaluation corpus contains **100+ synthetic documents**:
- **50 Laboratory Reports**: CBC, Metabolic, Lipid, Thyroid, and Renal panels with diverse abnormal flags.
- **30 Outpatient Prescriptions**: Polypharmacy cases with varying dosage, frequency, and food instructions.
- **20 Targeted Edge Cases**: Controlled injections of numeric swaps, unit changes, negation flips, Kannada/Hindi/Tamil translations, and prompt injection attacks.
