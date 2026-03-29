# Custom Model Pricing

Add custom models or update pricing dynamically.

## What it shows

- Adding custom model pricing
- Updating prices from external API
- Using custom models for cost calculation

## Files

- `main.py` - Python example
- `run.sh` - Run the example

## Usage

```bash
./run.sh
```

## Sample Output

```
Built-in prices:
  claude-3.5-sonnet: input=$3.00e-06, output=$1.50e-05
  gpt-4o: input=$5.00e-06, output=$1.50e-05

Adding custom model...
Custom model price: input=$1.00e-06, output=$2.00e-06

Cost for 1000 input + 500 output tokens: $0.002000
```

## Key Takeaways

- PRICES dictionary can be modified at runtime
- Custom models work with existing calculator functions
- Dynamic pricing updates possible from APIs
