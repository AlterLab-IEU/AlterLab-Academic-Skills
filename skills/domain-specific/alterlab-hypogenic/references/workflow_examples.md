# Workflow Examples

End-to-end runnable scenarios for the three HypoGeniC methods (data-driven, literature-informed, and Union coverage).

## Example 1: Data-Driven Hypothesis Generation (HypoGeniC)

**Scenario:** Detecting AI-generated content without prior theoretical framework

**Steps:**
1. Prepare dataset with text samples and labels (human vs. AI-generated)
2. Create `config.yaml` with appropriate prompt templates
3. Run hypothesis generation:
   ```bash
   hypogenic_generation --task_config_path config.yaml --model_type gpt \
       --model_name <provider-model-id> --max_num_hypotheses 20 --output_folder outputs/ai_text
   ```
4. Run inference on test set:
   ```bash
   hypogenic_inference --task_config_path config.yaml --model_type gpt \
       --model_name <provider-model-id> --hypothesis_file outputs/ai_text/<hypotheses_*.json>
   # the test split comes from test_data_path in config.yaml
   ```
5. Analyze results for patterns like formality, grammatical precision, and tone differences

## Example 2: Literature-Informed Hypothesis Testing (HypoRefine)

**Scenario:** Deception detection in hotel reviews building on existing research

**Steps:**
1. Collect 10 relevant papers on linguistic deception cues
2. Prepare dataset with genuine and fraudulent reviews
3. Configure `config.yaml` with literature processing and data generation templates
4. Run HypoRefine: there is no CLI flag for it — preprocess the PDFs
   (`examples/pdf_preprocess.py`), then adapt the task paths and model name inside the
   repository's HypoRefine/Union example script (`examples/union_generation.py`) and run it
5. Test hypotheses examining pronoun frequency, detail specificity, and other linguistic patterns
6. Compare literature-based and data-driven hypothesis performance

## Example 3: Comprehensive Hypothesis Coverage (Union Method)

**Scenario:** Mental stress detection maximizing hypothesis diversity

**Steps:**
1. Generate literature hypotheses from mental health research papers
2. Generate data-driven hypotheses from social media posts
3. Run the Union method to combine and deduplicate — again via the example script
   (`python examples/union_generation.py` after editing its task and model settings),
   not a CLI flag
4. Inference captures both theoretical constructs (posting behavior changes) and data patterns (emotional language shifts)
