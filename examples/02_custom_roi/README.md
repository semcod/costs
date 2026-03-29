# Custom ROI Analysis

Customize ROI calculations with different hourly rates and productivity metrics.

## What it shows

- Calculate ROI for different developer levels
- Customize hourly rates and review overhead
- Compare value generated across scenarios

## Files

- `main.py` - Python example
- `run.sh` - Run the example

## Usage

```bash
./run.sh
```

## Sample Output

```
Scenario                 Cost  Hours Saved        Value      ROI
----------------------------------------------------------------------
Junior Developer     $  0.50        1.3h $     65.62     105x
Senior Developer     $  0.50        1.0h $    150.00     360x
Consultant           $  0.50        1.1h $    281.25     562x

Key insight: Higher hourly rates = higher ROI, even with same AI cost
```

## Key Takeaways

- ROI scales with developer hourly rate
- Review overhead reduces effective savings
- Same AI cost, different value for different roles
