# Presentation Development Workflow

Six-stage process from planning to final preparation, plus integration with other skills and common pitfalls.

## Stage 1: Planning (Before Creating Slides)

**Define Context:**
1. What type of talk? (Conference, seminar, defense, etc.)
2. How long? (Duration in minutes)
3. Who is the audience? (Specialists, general, mixed)
4. What's the venue? (Room size, A/V setup, virtual/in-person)
5. What happens after? (Q&A, discussion, networking)

**Research and Literature Review** (Use research-lookup skill):
1. **Search for background literature**: Find 5-10 key papers establishing context
2. **Identify knowledge gaps**: Use research-lookup to find what's unknown
3. **Locate comparison studies**: Find papers with similar methods or results
4. **Gather supporting citations**: Collect papers supporting your interpretations
5. **Build reference list**: Create .bib file or citation list for slides
6. **Note key findings to cite**: Document specific results to reference

**Develop Content Outline:**
1. Identify 1-3 core messages
2. Select key findings to present
3. Choose essential figures (typically 3-6 for 15-min talk)
4. Plan narrative arc with proper citations
5. Allocate time by section

**Example Outline for 15-Minute Talk:**
```
1. Title (30 sec)
2. Hook: Compelling problem (60 sec) [Cite 1-2 papers via research-lookup]
3. Background (90 sec) [Cite 3-4 key papers establishing context]
4. Research question (45 sec) [Cite papers showing gap]
5. Methods overview (2 min)
6-8. Main result 1 (3 min, 3 slides)
9-10. Main result 2 (2 min, 2 slides)
11-12. Result 3 or validation (2 min, 2 slides)
13-14. Discussion and implications (2 min) [Compare to 2-3 prior studies]
15. Conclusions (45 sec)
16. Acknowledgments (15 sec)

NOTE: Use research-lookup to find papers for background (slides 2-4)
and discussion (slides 13-14) BEFORE creating slides.
```

## Stage 2: Design and Creation

**Choose Implementation Method:**

**Option A: PowerPoint (via PPTX skill)**
1. Read `assets/powerpoint_design_guide.md`
2. Read `document-skills/pptx/SKILL.md`
3. Choose approach (programmatic or template-based)
4. Create master slides with consistent design
5. Build presentation following outline

**Option B: LaTeX Beamer**
1. Read `references/beamer_guide.md`
2. Select appropriate template from `assets/`
3. Customize theme and colors
4. Write content in LaTeX
5. Compile to PDF

**Design Considerations** (Make It Visually Appealing):
- **Select MODERN color palette**: Match your topic (biotech=vibrant, physics=sleek, health=warm)
  - Use pptx skill's color palette examples (Teal & Coral, Bold Red, Deep Purple & Emerald, etc.)
  - NOT just default blue/gray themes
  - 3-5 colors with high contrast
- **Choose clean fonts**: Sans-serif, large sizes (24pt+ body)
- **Plan visual elements**: What images, diagrams, icons for each slide?
- **Create varied layouts**: Mix full-figure, two-column, text-overlay (not all bullets)
- **Design section dividers**: Visual breaks with striking graphics
- **Plan animations/builds**: Control information flow for complex slides
- **Add visual interest**: Background images, color blocks, shapes, icons

## Stage 3: Content Development

**Populate Slides** (Visual-First Strategy):
1. **Start with visuals**: Plan which figures, images, diagrams for each key point
2. **Use research-lookup extensively**: Find 8-15 papers for proper citations
3. **Create visual backbone first**: Add all figures, charts, images, diagrams
4. **Add minimal text as support**: Bullet points complement visuals, don't replace them
5. **Design section dividers**: Visual breaks with images or graphics (not just text)
6. **Polish title/closing**: Make visually striking, include contact info
7. **Add transitions/builds**: Control information flow

**VISUAL CONTENT REQUIREMENTS** (Make Slides Engaging):
- **Images**: Use high-quality photos, illustrations, conceptual graphics
- **Icons**: Visual representations of concepts (not decoration)
- **Diagrams**: Flowcharts, schematics, process diagrams
- **Figures**: Simplified research figures with LARGE labels (18-24pt)
- **Charts**: Clean data visualizations with clear messages
- **Graphics**: Visual metaphors, conceptual illustrations
- **Color blocks**: Use colored shapes to organize content visually
- Target: MINIMUM 1-2 strong visual elements per slide

**Scientific Content** (Research-Backed):
- **Citations**: Use research-lookup EXTENSIVELY to find relevant papers
  - Introduction: Cite 3-5 papers establishing context and gap
  - Background: Show key prior work visually (not just cite)
  - Discussion: Cite 3-5 papers for comparison with your results
  - Use author-year format (Smith et al., 2023) for readability
  - Citations establish credibility and scientific rigor
- **Figures**: Simplified from papers, LARGE labels (18-24pt minimum)
- **Equations**: Large, clear, explain each term (use sparingly)
- **Tables**: Minimal, highlight key comparisons (not data dumps)
- **Code/Algorithms**: Use syntax highlighting, keep brief

**Text Guidelines** (Less is More):
- Bullet points, NEVER paragraphs
- 3-4 bullets per slide (max 6 only if essential)
- 4-6 words per bullet (shorter than 6×6 rule)
- Key terms in bold
- Text is SUPPORTING ROLE, visuals are stars
- Use builds to control pacing

## Stage 4: Visual Validation

**Generate Images:**
```bash
# Convert PDF to images (export PowerPoint to PDF first)
python scripts/pdf_to_images.py presentation.pdf review/slides
```

**Systematic Review:**
1. View each slide image
2. Check against issue checklist
3. Document problems with slide numbers
4. Test readability from distance (view at 50% size)

**Common Issues to Fix**: text beyond boundaries, figures overlapping text, fonts too small, poor contrast, misalignment.

**Iteration**: fix issues in source → regenerate PDF/presentation → convert to images again → re-inspect → repeat until clean.

## Stage 5: Practice and Refinement

**Practice Schedule:**
- Run 1: Rough draft (will run long)
- Run 2: Smooth transitions
- Run 3: Exact timing
- Run 4: Final polish
- Run 5+: Maintenance (day before, morning of)

**What to Practice**: full talk with timer, difficult explanations, transitions between sections, opening and closing (until flawless), anticipated questions.

**Refinement Based on Practice**: cut slides if running over, expand explanations if unclear, adjust wording for clarity, mark timing checkpoints, prepare backup slides.

## Stage 6: Final Preparation

**Technical Checks:**
- [ ] Multiple copies saved (laptop, cloud, USB)
- [ ] Works on presentation computer
- [ ] Adapters/cables available
- [ ] Backup PDF version
- [ ] Tested with projector (if possible)

**Content Final:**
- [ ] No typos or errors
- [ ] All figures high quality
- [ ] Slide numbers correct
- [ ] Contact info on final slide
- [ ] Backup slides ready

**Delivery Prep:**
- [ ] Notes prepared (if using)
- [ ] Timer/phone ready
- [ ] Water available
- [ ] Business cards/handouts
- [ ] Comfortable with material (3+ practices)

## Integration with Other Skills

**Research Lookup** (Critical for Scientific Presentations):
- **Background development**: Search literature to build introduction context
- **Citation gathering**: Find key papers to cite in your talk
- **Gap identification**: Identify what's unknown to motivate research
- **Prior work comparison**: Find papers to compare your results against
- **Supporting evidence**: Locate literature supporting your interpretations
- **Question preparation**: Find papers that might inform Q&A responses
- **Always use research-lookup** when developing any scientific presentation to ensure proper context and citations

**Scientific Writing**: convert paper content to presentation format, extract key findings and simplify, use same figures (redesigned for slides), maintain consistent terminology.

**PPTX Skill**: use for PowerPoint creation and editing, leverage scripts for template workflows, use thumbnail generation for validation, reference html2pptx for programmatic creation.

**Data Visualization**: create presentation-appropriate figures, simplify complex visualizations, ensure readability from distance, use progressive disclosure.

## Common Pitfalls to Avoid

### Content Mistakes

**Dry, Boring Presentations** (CRITICAL TO AVOID):
- Problem: Text-heavy slides with no visual interest, missing research context
- Signs: All bullet points, no images, default templates, no citations
- Solution: Use research-lookup to find 8-15 papers for credible context; add high-quality visuals to EVERY slide; choose modern color palette; vary slide layouts; tell a story with visuals, use text sparingly

**Too Much Content**: trying to include everything from paper → focus on 1-2 key findings for short talks, show visually.

**Too Much Text**: full paragraphs, dense bullets, reading verbatim → 3-4 bullets with 4-6 words each, let visuals carry the message.

**Missing Research Context**: no citations, claims without support → use research-lookup, cite 3-5 in intro, 3-5 in discussion.

**Poor Narrative**: jumping between topics, no flow → follow story arc, use visual transitions, maintain thread.

**Rushing Through Results**: brief results, long discussion → spend 40-50% of time on results, show data visually.

### Design Mistakes

**Generic, Default Appearance**: default themes uncustomized → choose modern color palette, customize fonts/layouts, add visual personality.

**Text-Heavy, Visual-Poor**: all bullet slides, no graphics → add figures, photos, diagrams, icons to EVERY slide.

**Small Fonts**: body <18pt → 24-28pt for body, 36-44pt for titles.

**Low Contrast**: light text on light background → high contrast (7:1 preferred), test with contrast checker.

**Cluttered Slides**: too many elements, no white space → one idea per slide, 40-50% white space.

**Inconsistent Formatting**: different fonts/colors slide-to-slide → use master slides, maintain design system.

**Missing Visual Hierarchy**: everything same size/color → size differences, color for emphasis, clear focal point.

### Timing Mistakes

**Not Practicing**: first time through is during presentation → practice minimum 3 times with timer.

**No Time Checkpoints**: don't realize running behind → set 3-4 checkpoints, monitor throughout.

**Going Over Time**: cuts into Q&A → practice to exact time, prepare Plan B (slides to skip).

**Skipping Conclusions**: rush through or skip ending → never skip conclusions, cut earlier content instead.
