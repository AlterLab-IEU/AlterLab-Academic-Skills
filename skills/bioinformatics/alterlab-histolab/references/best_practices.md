# Histolab Best Practices, Use Cases & Troubleshooting

## Best Practices

### Slide Loading and Inspection
1. Always inspect slide properties before processing
2. Save thumbnails for quick visual review
3. Check pyramid levels and dimensions
4. Verify tissue is present using thumbnails

### Tissue Detection
1. Preview masks with `locate_mask()` before extraction
2. Use `TissueMask` for multiple sections, `BiggestTissueBoxMask` for single sections
3. Customize filters for specific stains (H&E vs IHC)
4. Handle pen annotations with custom masks
5. Test masks on diverse slides

### Tile Extraction
1. **Always preview with `locate_tiles()` before extracting**
2. Choose appropriate tiler:
   - RandomTiler: Sampling and exploration
   - GridTiler: Complete coverage
   - ScoreTiler: Quality-driven selection
3. Set appropriate `tissue_percent` threshold (70-90% typical)
4. Use seeds for reproducibility in RandomTiler
5. Extract at appropriate pyramid level for analysis resolution
6. Enable logging for large datasets

### Performance
1. Extract at lower levels (1, 2) for faster processing
2. Use `BiggestTissueBoxMask` over `TissueMask` when appropriate
3. Adjust `tissue_percent` to reduce invalid tile attempts
4. Limit `n_tiles` for initial exploration
5. Use `pixel_overlap=0` for non-overlapping grids

### Quality Control
1. Validate tile quality (check for blur, artifacts, focus)
2. Review score distributions for ScoreTiler
3. Inspect top and bottom scoring tiles
4. Monitor tissue coverage statistics
5. Filter extracted tiles by additional quality metrics if needed

## Common Use Cases

### Training Deep Learning Models
- Extract balanced datasets using RandomTiler across multiple slides
- Use ScoreTiler with NucleiScorer to focus on cell-rich regions
- Extract at consistent resolution (level 0 or level 1)
- Generate CSV reports for tracking tile metadata

### Whole Slide Analysis
- Use GridTiler for complete tissue coverage
- Extract at multiple pyramid levels for hierarchical analysis
- Maintain spatial relationships with grid positions
- Use `pixel_overlap` for sliding window approaches

### Tissue Characterization
- Sample diverse regions with RandomTiler
- Quantify tissue coverage with masks
- Extract stain-specific information with HED decomposition
- Compare tissue patterns across slides

### Quality Assessment
- Identify optimal focus regions with ScoreTiler
- Detect artifacts using custom masks and filters
- Assess staining quality across slide collection
- Flag problematic slides for manual review

### Dataset Curation
- Use ScoreTiler to prioritize informative tiles
- Filter tiles by tissue percentage
- Generate reports with tile scores and metadata
- Create stratified datasets across slides and tissue types

## Troubleshooting

### No tiles extracted
- Lower `tissue_percent` threshold
- Verify slide contains tissue (check thumbnail)
- Ensure extraction_mask captures tissue regions
- Check tile_size is appropriate for slide resolution

### Many background tiles
- Enable `check_tissue=True`
- Increase `tissue_percent` threshold
- Use appropriate mask (TissueMask vs BiggestTissueBoxMask)
- Customize mask filters to better detect tissue

### Extraction very slow
- Extract at lower pyramid level (level=1 or 2)
- Reduce `n_tiles` for RandomTiler/ScoreTiler
- Use RandomTiler instead of GridTiler for sampling
- Use BiggestTissueBoxMask instead of TissueMask

### Tiles have artifacts
- Implement custom annotation-exclusion masks
- Adjust filter parameters for artifact removal
- Increase small object removal threshold
- Apply post-extraction quality filtering

### Inconsistent results across slides
- Use same seed for RandomTiler
- Normalize staining with preprocessing filters
- Adjust `tissue_percent` per staining quality
- Implement slide-specific mask customization
