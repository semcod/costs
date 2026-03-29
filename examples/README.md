# Examples

This directory contains usage examples for the `costs` AI cost tracking library.

Each example is in its own directory with:
- `README.md` - Explanation of the example
- `main.py` or script file - The example code
- `run.sh` - Script to run the example

## Directory Structure

```
examples/
├── 01_tokenizer_basic/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 02_multi_model_cost/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 03_batch_processing/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 04_basic_usage/
│   ├── README.md
│   └── run.sh
├── 05_badge_generation/
│   ├── README.md
│   └── run.sh
├── 06_diff_estimation/
│   ├── README.md
│   └── run.sh
├── 07_pre-commit-hook/
│   ├── README.md
│   ├── pre-commit
│   ├── install.sh
│   └── run.sh
├── 08_github-actions/
│   ├── README.md
│   ├── workflow.yml
│   └── run.sh
├── 09_gitlab-ci/
│   ├── README.md
│   ├── .gitlab-ci.yml
│   └── run.sh
├── 10_custom_pricing/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 11_custom_roi/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 12_multi_repo/
│   ├── README.md
│   ├── main.py
│   └── run.sh
├── 13_cost_trends/
│   ├── README.md
│   ├── main.py
│   └── run.sh
└── README.md
```

## Quick Start

### API Examples

```bash
# Run basic tokenizer example
cd examples/api/01_tokenizer_basic
./run.sh

# Or run directly
python3 main.py
```

### CLI Examples

```bash
cd examples/cli/01_basic_usage
./run.sh
```

### Integration Examples

```bash
# Install pre-commit hook
cd examples/integration/pre-commit-hook
./install.sh
```

### Advanced Examples

```bash
cd examples/advanced/01_custom_pricing
./run.sh
```

## Examples by Category

### API Usage (Python)

| Example | Description |
|---------|-------------|
| `01_tokenizer_basic/` | Basic token counting with different models |
| `02_multi_model_cost/` | Compare costs across providers |
| `03_batch_processing/` | Process multiple commits in batch |

### CLI Usage (Shell)

| Example | Description |
|---------|-------------|
| `01_basic_usage/` | Common CLI commands |
| `02_badge_generation/` | Badge and report generation |
| `03_diff_estimation/` | Single diff estimation |

### Integration

| Example | Description |
|---------|-------------|
| `pre-commit-hook/` | Auto-update badge on commit |
| `github-actions/` | GitHub Actions workflow |
| `gitlab-ci/` | GitLab CI configuration |

### Advanced

| Example | Description |
|---------|-------------|
| `01_custom_pricing/` | Add custom model pricing |
| `02_custom_roi/` | Custom ROI calculations |
| `03_multi_repo/` | Analyze multiple repositories |
| `04_cost_trends/` | Cost analytics and projections |

## Running Examples

All examples can be run using the provided `run.sh` script:

```bash
cd examples/<category>/<example>
./run.sh
```

Or run Python examples directly:

```bash
cd examples/api/01_tokenizer_basic
python3 main.py
```

## Notes

- API examples use the `costs` Python package
- CLI examples show shell commands (bash/sh compatible)
- Integration examples may need customization for your environment
- Advanced examples demonstrate extending the library
- Each example has its own README with detailed explanation
