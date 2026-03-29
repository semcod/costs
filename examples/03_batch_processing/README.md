# Batch Processing

Process multiple commits/diffs in batch with cost aggregation.

## What it shows

- Processing multiple commits in a batch
- Aggregating costs across commits
- Calculating total tokens and cost
- Estimating value generated from batch

## Usage

```bash
./run.sh
```

## Sample Output

```
Commit     Message                   Tokens      Cost
----------------------------------------------------------------------
abc1234    Fix authentication bug        145 $   0.000435
def5678    Add rate limiting             298 $   0.000894
ghi9012    Update API documentation      189 $   0.000567
----------------------------------------------------------------------
TOTAL                                  632 $   0.001896

Value generated: $0.19 (100x ROI assumption)
Average per commit: $0.000632
```

## Use Cases

- Monthly cost reporting
- Team productivity analysis
- Budget planning and forecasting
