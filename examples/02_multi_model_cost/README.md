# Multi-Model Cost Comparison

Compare costs across different LLM providers for the same code diff.

## What it shows

- Estimating tokens for realistic code changes
- Calculating costs using actual model pricing
- Comparing costs across providers (OpenAI, Anthropic, OpenRouter)
- Understanding cost differences for the same work

## Usage

```bash
./run.sh
```

## Sample Output

```
Model                             Input   Output         Cost
----------------------------------------------------------------------
GPT-4o                              314      510 $  0.009220
Claude 3.5 Sonnet                   314      510 $  0.008592
Claude 3.5 Haiku                    314      510 $  0.002291
Qwen3 Coder Next                    314      510 $  0.000922
GPT-4o Mini                         314      510 $  0.000353
```

## Key Insights

- Input tokens are the same across models (same tokenizer used)
- Output tokens estimated based on added lines (~30 tokens per line)
- Cost varies 26x between most and least expensive option
- Haiku and Qwen3 Coder offer excellent value for code review
