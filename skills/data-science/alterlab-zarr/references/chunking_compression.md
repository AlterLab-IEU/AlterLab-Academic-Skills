# Zarr Chunking, Compression, and Sharding

Chunking is critical for performance. Choose chunk sizes and shapes based on access patterns.

## Chunk Size Guidelines

- **Minimum chunk size**: 1 MB recommended for optimal performance
- **Balance**: Larger chunks = fewer metadata operations; smaller chunks = better parallel access
- **Memory consideration**: Entire chunks must fit in memory during compression

```python
# Configure chunk size (aim for ~1MB per chunk)
# For float32 data: 1MB = 262,144 elements = 512×512 array
z = zarr.zeros(
    shape=(10000, 10000),
    chunks=(512, 512),  # ~1MB chunks
    dtype='f4'
)
```

## Aligning Chunks with Access Patterns

**Critical**: Chunk shape dramatically affects performance based on how data is accessed.

```python
# If accessing rows frequently (first dimension)
z = zarr.zeros((10000, 10000), chunks=(10, 10000))  # Chunk spans columns

# If accessing columns frequently (second dimension)
z = zarr.zeros((10000, 10000), chunks=(10000, 10))  # Chunk spans rows

# For mixed access patterns (balanced approach)
z = zarr.zeros((10000, 10000), chunks=(1000, 1000))  # Square chunks
```

**Performance example**: For a (200, 200, 200) array, reading along the first dimension:
- Using chunks (1, 200, 200): ~107ms
- Using chunks (200, 200, 1): ~1.65ms (65× faster!)

## Sharding for Large-Scale Storage

When arrays have millions of small chunks, use sharding to group chunks into larger storage objects:

```python
from zarr.codecs import ShardingCodec, BytesCodec
from zarr.codecs.blosc import BloscCodec

# Create array with sharding
z = zarr.create_array(
    store='data.zarr',
    shape=(100000, 100000),
    chunks=(100, 100),  # Small chunks for access
    shards=(1000, 1000),  # Groups 100 chunks per shard
    dtype='f4'
)
```

**Benefits**:
- Reduces file system overhead from millions of small files
- Improves cloud storage performance (fewer object requests)
- Prevents filesystem block size waste

**Important**: Entire shards must fit in memory before writing.

## Compression

Zarr applies compression per chunk to reduce storage while maintaining fast access.

### Configuring Compression

```python
from zarr.codecs.blosc import BloscCodec
from zarr.codecs import GzipCodec, ZstdCodec

# Default: Blosc with Zstandard
z = zarr.zeros((1000, 1000), chunks=(100, 100))  # Uses default compression

# Configure Blosc codec
z = zarr.create_array(
    store='data.zarr',
    shape=(1000, 1000),
    chunks=(100, 100),
    dtype='f4',
    codecs=[BloscCodec(cname='zstd', clevel=5, shuffle='shuffle')]
)

# Available Blosc compressors: 'blosclz', 'lz4', 'lz4hc', 'snappy', 'zlib', 'zstd'

# Use Gzip compression
z = zarr.create_array(
    store='data.zarr',
    shape=(1000, 1000),
    chunks=(100, 100),
    dtype='f4',
    codecs=[GzipCodec(level=6)]
)

# Disable compression
z = zarr.create_array(
    store='data.zarr',
    shape=(1000, 1000),
    chunks=(100, 100),
    dtype='f4',
    codecs=[BytesCodec()]  # No compression
)
```

### Compression Performance Tips

- **Blosc** (default): Fast compression/decompression, good for interactive workloads
- **Zstandard**: Better compression ratios, slightly slower than LZ4
- **Gzip**: Maximum compression, slower performance
- **LZ4**: Fastest compression, lower ratios
- **Shuffle**: Enable shuffle filter for better compression on numeric data

```python
# Optimal for numeric scientific data
codecs=[BloscCodec(cname='zstd', clevel=5, shuffle='shuffle')]

# Optimal for speed
codecs=[BloscCodec(cname='lz4', clevel=1)]

# Optimal for compression ratio
codecs=[GzipCodec(level=9)]
```
