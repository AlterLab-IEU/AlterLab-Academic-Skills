# Creating Custom Tasks

Step-by-step guide for adding a new task or dataset to Hypogenic, including dataset prep, config authoring, and a custom `extract_label` implementation.

To add a new task or dataset to Hypogenic:

## Step 1: Prepare Your Dataset

Create three JSON files following the required format:
- `your_task_train.json`
- `your_task_val.json`
- `your_task_test.json`

Each file must have keys for text features (`text_features_1`, etc.) and `label`.

## Step 2: Create config.yaml

Define your task configuration with:
- Task name and dataset paths
- Prompt templates for observations, generation, inference
- Any extra keys for reusable prompt components
- Placeholder variables (e.g., `${text_features_1}`, `${num_hypotheses}`)

## Step 3: Implement extract_label Function

Create a custom label extraction function that parses LLM outputs for your domain:

```python
from hypogenic.tasks import BaseTask

def extract_my_label(llm_output: str) -> str:
    """Custom label extraction for your task.
    
    Must return labels in same format as dataset 'label' field.
    """
    # Example: Extract from specific format
    if "Final prediction:" in llm_output:
        return llm_output.split("Final prediction:")[-1].strip()
    
    # Fallback to default pattern
    import re
    match = re.search(r'final answer:\s+(.*)', llm_output, re.IGNORECASE)
    return match.group(1).strip() if match else llm_output.strip()

# Use your custom task (first positional arg is the config path)
task = BaseTask("./your_task/config.yaml", extract_label=extract_my_label)
```

## Step 4: (Optional) Process Literature

For HypoRefine/Union methods:
1. Create `literature/your_task_name/raw/` directory
2. Add relevant research paper PDFs
3. Run GROBID preprocessing
4. Process with `pdf_preprocess.py`

## Step 5: Generate and Test

Run hypothesis generation and inference using CLI or Python API:

```bash
# CLI approach
hypogenic_generation --config your_task/config.yaml --method hypogenic --num_hypotheses 20
hypogenic_inference --config your_task/config.yaml --hypotheses output/hypotheses.json

# Or use Python API (see references/python_api.md)
```
