# Running evals on a local model (defect sweeps)

A local model can run the behavioral harness for free and without usage limits. Use it to
find **eval and environment defects**: prompts that refer to input they do not ship, tool
grants a skill lacks, scripts that crash, dependencies that will not install, hosts that
cannot be reached. Those failures do not depend on which model answers, and fixing them is
most of the work of getting a skill to pass.

A local run says nothing about whether a skill makes **Claude** better than bare Claude. Its
pass/fail numbers describe the local model plus the skill. Never report them as skill
quality, and never mix them with Claude results. The run record's `endpoint` field says which
backend answered.

## The setup this was written for

- A Windows workstation with an RTX 5090 (32 GB), running llama-swap on `127.0.0.1:8080`
  with `qwen3.8-27b` (128K context, about 31 GB of VRAM). Its chat template must accept the
  mid-conversation `system` messages Claude Code sends. A stock Qwen template returns 500 on
  every request.
- **WSL2 Ubuntu** as the runner, not native Windows. The harness hides this checkout from
  answer arms with a Linux mount namespace. On Windows it falls back to scoped Write/Edit
  grants and a tripwire, and shell grants could then reach any folder on the machine. The
  skills' scripts also assume POSIX tools (`bash`, `uv`, `python3`).

## Steps

1. **A disposable checkout** inside WSL — never your working copy:

   ```bash
   git clone <repo-url> ~/evals/alterlab && cd ~/evals/alterlab
   uv sync
   ```

2. **Start the model server** on Windows. Check `nvidia-smi` first, and close ComfyUI and
   other GPU work. For two parallel requests, serve 2 slots of 64K each (`-np 2`, with the
   context at 131072 split across them). Claude Code needs about 30–40K of context per arm.

3. **Point the CLI at it** from WSL. This needs mirrored networking, so `127.0.0.1` reaches
   Windows; otherwise use the host IP:

   ```bash
   export ANTHROPIC_BASE_URL=http://127.0.0.1:8080
   export ANTHROPIC_AUTH_TOKEN=local          # llama-swap's placeholder, not an Anthropic key
   export ALTERLAB_MODEL=qwen3.8-27b
   claude -p "Reply with the word ready." --output-format json | head -c 300   # smoke test
   ```

4. **Check a judge before using one.** A collect-only sweep needs no judge. If you want the
   local model to judge as well, it must agree with every hand-labelled pair first:

   ```bash
   uv run python scripts/run_evals.py --calibrate-judge    # must print 8/8 for the judge you use
   ```

5. **Pilot on skills Claude has already been run on**, and compare the defect lists:

   ```bash
   printf "skills/turkish-academia/alterlab-trdizin\nskills/social-science-workflow/alterlab-sem-psychometrics\n" > pilot.txt
   scripts/eval_sweep.sh pilot.txt 2 eval-results/local-qwen/pilot --runs 1 --timeout 900 --collect-only
   uv run python scripts/defect_scan.py eval-results/local-qwen/pilot
   ```

   Go on only if the local run flags most of the defects a Claude run of the same skills
   found. If the local model misuses tools often enough to drown the real defects, stop: its
   defect list would mislead.

6. **The sweep**, with collect-only answers and no judges. Expect hours per domain:

   ```bash
   scripts/eval_sweep.sh list.txt 2 eval-results/local-qwen/sweep --runs 1 --timeout 900 --collect-only
   uv run python scripts/defect_scan.py eval-results/local-qwen/sweep --json eval-results/local-qwen/defects.json
   ```

   `list.txt` has one skill directory per line. `--timeout 900` allows for a slower model.

7. **Hand back** `eval-results/local-qwen/defects.json` and the results directory. Fixes go
   into the skills and evals; the verdict run that is reported is a Claude run.

8. **Stop the model server** afterwards and confirm VRAM is released.

## What the defect categories mean

| Category | Usual fix |
|---|---|
| `input_missing` | Ship the input as a fixture (`files`), or make the prompt self-contained |
| `tool_denied` | Read `denied_tools`: add the grant to the skill's `allowed-tools`, or teach the skill a permitted route (e.g. `uv run --with` instead of `pip install`) |
| `install_blocked` | A `uv run --python ">=3.11" --with <pkg>` recipe in the skill |
| `script_error` | Fix the bundled script, or the call the skill documents |
| `network_blocked` | Tag the eval `requires: ["net:<host>"]`, or give the skill an offline path |
| `no_answer` | Timeout, CLI failure or usage limit: re-run, or raise `--timeout` |
