# BRENDA — Data Formats, Parsing & Best Practices

## BRENDA Response Format

BRENDA returns data in specific delimited formats that need parsing.

**Km Value Format**:
```
organism*Escherichia coli#substrate*ethanol#kmValue*1.2#kmValueMaximum*#commentary*pH 7.4, 25°C#ligandStructureId*#literature*
```

**Reaction Format**:
```
ecNumber*1.1.1.1#organism*Saccharomyces cerevisiae#reaction*ethanol + NAD+ <=> acetaldehyde + NADH + H+#commentary*#literature*
```

## Data Extraction Patterns

```python
import re

def parse_brenda_field(data, field_name):
    """Extract specific field from BRENDA data entry"""
    pattern = f"{field_name}\\*([^#]*)"
    match = re.search(pattern, data)
    return match.group(1) if match else None

def extract_multiple_values(data, field_name):
    """Extract multiple values for a field"""
    pattern = f"{field_name}\\*([^#]*)"
    matches = re.findall(pattern, data)
    return [match for match in matches if match.strip()]
```

## API Rate Limits and Best Practices

**Rate Limits**:
- BRENDA API has moderate rate limiting
- Recommended: 1 request per second for sustained usage
- Maximum: 5 requests per 10 seconds

**Best Practices**:
1. **Cache results**: Store frequently accessed enzyme data locally
2. **Batch queries**: Combine related requests when possible
3. **Use specific searches**: Narrow down by organism, substrate when possible
4. **Handle missing data**: Not all enzymes have complete data
5. **Validate EC numbers**: Ensure EC numbers are in correct format
6. **Implement delays**: Add delays between consecutive requests
7. **Use wildcards wisely**: Use '*' for broader searches when appropriate
8. **Monitor quota**: Track your API usage

**Error Handling**:
```python
from scripts.brenda_client import get_km_values, get_reactions
from zeep.exceptions import Fault, TransportError

try:
    km_data = get_km_values("1.1.1.1")
except RuntimeError as e:
    print(f"Authentication error: {e}")
except Fault as e:
    print(f"BRENDA API error: {e}")
except TransportError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Troubleshooting

**Authentication Errors**:
- Verify BRENDA_EMAIL and BRENDA_PASSWORD in .env file
- Check for correct spelling (note BRENDA_EMIAL legacy support)
- Ensure BRENDA account is active and has API access

**No Results Returned**:
- Try broader searches with wildcards (*)
- Check EC number format (e.g., "1.1.1.1" not "1.1.1")
- Verify substrate spelling and naming
- Some enzymes may have limited data in BRENDA

**Rate Limiting**:
- Add delays between requests (0.5-1 second)
- Cache results locally
- Use more specific queries to reduce data volume
- Consider batch operations for multiple queries

**Network Errors**:
- Check internet connection
- BRENDA server may be temporarily unavailable
- Try again after a few minutes
- Consider using VPN if geo-restricted

**Data Format Issues**:
- Use the provided parsing functions in scripts
- BRENDA data can be inconsistent in formatting
- Handle missing fields gracefully
- Validate parsed data before use

**Performance Issues**:
- Large queries can be slow; limit search scope
- Use specific organism or substrate filters
- Consider asynchronous processing for batch operations
- Monitor memory usage with large datasets

## Additional Resources

- BRENDA Home: https://www.brenda-enzymes.org/
- BRENDA SOAP API Documentation: https://www.brenda-enzymes.org/soap.php
- Enzyme Commission (EC) Numbers: https://www.qmul.ac.uk/sbcs/iubmb/enzyme/
- Zeep SOAP Client: https://python-zeep.readthedocs.io/
- Enzyme Nomenclature: https://www.iubmb.org/enzyme/
