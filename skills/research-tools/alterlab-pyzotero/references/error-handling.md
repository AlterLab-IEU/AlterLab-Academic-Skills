# Error Handling

## Exception Types

Pyzotero raises subclasses of `PyZoteroError` (the base class) for API errors. Import from `pyzotero.errors`:

```python
from pyzotero import errors
```

All exception class names end in `Error` (verified against pyzotero 1.13). Common exceptions:

| Exception | Cause |
|-----------|-------|
| `UserNotAuthorisedError` | Invalid or missing API key |
| `HTTPError` | Generic HTTP error |
| `ParamNotPassedError` | Required parameter missing |
| `CallDoesNotExistError` | Invalid API method for library type |
| `ResourceNotFoundError` | Item/collection key not found |
| `ConflictError` | Version conflict (optimistic locking) |
| `PreConditionFailedError` | `If-Unmodified-Since-Version` check failed |
| `TooManyItemsError` | Batch exceeds 50-item limit |
| `TooManyRequestsError` | API rate limit exceeded |
| `InvalidItemFieldsError` | Item dict contains unknown fields |

## Basic Error Handling

```python
from pyzotero import Zotero
from pyzotero import errors

zot = Zotero('123456', 'user', 'APIKEY')

try:
    item = zot.item('BADKEY')
except errors.ResourceNotFoundError:
    print('Item not found')
except errors.UserNotAuthorisedError:
    print('Invalid API key')
except Exception as e:
    print(f'Unexpected error: {e}')
    if hasattr(e, '__cause__'):
        print(f'Caused by: {e.__cause__}')
```

## Version Conflict Handling

```python
try:
    zot.update_item(item)
except errors.PreConditionFailedError:
    # Item was modified since you retrieved it — re-fetch and retry
    fresh_item = zot.item(item['data']['key'])
    fresh_item['data']['title'] = new_title
    zot.update_item(fresh_item)
```

## Checking for Invalid Fields

```python
from pyzotero import errors

template = zot.item_template('journalArticle')
template['badField'] = 'bad value'

try:
    zot.check_items([template])
except errors.InvalidItemFieldsError as e:
    print(f'Invalid fields: {e}')
    # Fix fields before calling create_items
```

## Rate Limiting

The Zotero API rate-limits requests. If you receive `TooManyRequestsError`:

```python
import time
from pyzotero import errors

def safe_request(func, *args, **kwargs):
    retries = 3
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except errors.TooManyRequestsError:
            wait = 2 ** attempt
            print(f'Rate limited, waiting {wait}s...')
            time.sleep(wait)
    raise RuntimeError('Max retries exceeded')

items = safe_request(zot.items, limit=100)
```

## Accessing Underlying Error

```python
try:
    zot.item('BADKEY')
except Exception as e:
    print(e.__cause__)    # original HTTP error
    print(e.__context__)  # exception context
```
