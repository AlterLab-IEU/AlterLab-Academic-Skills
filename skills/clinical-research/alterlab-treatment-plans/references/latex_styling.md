# LaTeX Styling: medical_treatment_plan.sty

This reference covers the optional professional medical document styling package and its colored box / table environments. It was moved out of `SKILL.md` to keep the skill body concise. See `SKILL.md` for when to use treatment-plan formats; use this file when you need the LaTeX styling details.

## Overview

Treatment plans can be enhanced with professional medical document styling using the `medical_treatment_plan.sty` LaTeX package. This custom style transforms plain academic documents into visually appealing, color-coded clinical documents that maintain scientific rigor while improving readability and usability.

## Medical Treatment Plan Style Package

The `medical_treatment_plan.sty` package (located in `assets/medical_treatment_plan.sty`) provides:

**Professional Color Scheme**
- **Primary Blue** (RGB: 0, 102, 153): Headers, section titles, primary accents
- **Secondary Blue** (RGB: 102, 178, 204): Light backgrounds, subtle accents
- **Accent Blue** (RGB: 0, 153, 204): Hyperlinks, key highlights
- **Success Green** (RGB: 0, 153, 76): Goals, positive outcomes
- **Warning Red** (RGB: 204, 0, 0): Warnings, critical information
- **Dark Gray** (RGB: 64, 64, 64): Body text
- **Light Gray** (RGB: 245, 245, 245): Background fills

**Styled Elements**
- Custom colored headers and footers with professional rules
- Blue section titles with underlines for clear hierarchy
- Enhanced table formatting with colored headers and alternating rows
- Optimized list spacing with colored bullets and numbering
- Professional page layout with appropriate margins

## Custom Information Boxes

The style package includes five specialized box environments for organizing clinical information:

### 1. Info Box (Blue Border, Light Gray Background)

For general information, clinical assessments, and testing schedules:

```latex
\begin{infobox}[Title]
  \textbf{Key Information:}
  \begin{itemize}
    \item Clinical assessment details
    \item Testing schedules
    \item General guidance
  \end{itemize}
\end{infobox}
```

**Use cases**: Metabolic status, baseline assessments, monitoring schedules, titration protocols

### 2. Warning Box (Red Border, Yellow Background)

For critical decision points, safety protocols, and alerts:

```latex
\begin{warningbox}[Alert Title]
  \textbf{Important Safety Information:}
  \begin{itemize}
    \item Critical drug interactions
    \item Safety monitoring requirements
    \item Red flag symptoms requiring immediate action
  \end{itemize}
\end{warningbox}
```

**Use cases**: Medication safety, decision points, contraindications, emergency protocols

### 3. Goal Box (Green Border, Green-Tinted Background)

For treatment goals, targets, and success criteria:

```latex
\begin{goalbox}[Treatment Goals]
  \textbf{Primary Objectives:}
  \begin{itemize}
    \item Reduce HbA1c to <7\% within 3 months
    \item Achieve 5-7\% weight loss in 12 weeks
    \item Complete diabetes education program
  \end{itemize}
\end{goalbox}
```

**Use cases**: SMART goals, target outcomes, success metrics, CGM goals

### 4. Key Points Box (Blue Background)

For executive summaries, key takeaways, and important recommendations:

```latex
\begin{keybox}[Key Highlights]
  \textbf{Essential Points:}
  \begin{itemize}
    \item Main therapeutic approach
    \item Critical patient instructions
    \item Priority interventions
  \end{itemize}
\end{keybox}
```

**Use cases**: Plan overview, plate method instructions, important dietary guidelines

### 5. Emergency Box (Large Red Design)

For emergency contacts and urgent protocols:

```latex
\begin{emergencybox}
  \begin{itemize}
    \item \textbf{Emergency Services:} 911
    \item \textbf{Endocrinology Office:} [Phone] (business hours)
    \item \textbf{After-Hours Hotline:} [Phone] (nights/weekends)
    \item \textbf{Pharmacy:} [Phone and location]
  \end{itemize}
\end{emergencybox}
```

**Use cases**: Emergency contacts, critical hotlines, urgent resource information

### 6. Patient Info Box (White with Blue Border)

For patient demographics and baseline information:

```latex
\begin{patientinfo}
  \begin{tabular}{ll}
    \textbf{Age:} & 23 years \\
    \textbf{Sex:} & Male \\
    \textbf{Diagnosis:} & Type 2 Diabetes Mellitus \\
    \textbf{Plan Start Date:} & \today \\
  \end{tabular}
\end{patientinfo}
```

**Use cases**: Patient information sections, demographic data

## Professional Table Formatting

Enhanced table environment with medical styling:

```latex
\begin{medtable}{Caption Text}
\begin{tabular}{|p{5cm}|p{4cm}|p{4.5cm}|}
\hline
\tableheadercolor  % Blue header with white text
\textcolor{white}{\textbf{Column 1}} & 
\textcolor{white}{\textbf{Column 2}} & 
\textcolor{white}{\textbf{Column 3}} \\
\hline
Data row 1 content & Value 1 & Details 1 \\
\hline
\tablerowcolor  % Alternating light gray row
Data row 2 content & Value 2 & Details 2 \\
\hline
Data row 3 content & Value 3 & Details 3 \\
\hline
\end{tabular}
\caption{Table caption}
\end{medtable}
```

**Features:**
- Blue headers with white text for visual prominence
- Alternating row colors (`\tablerowcolor`) for improved readability
- Automatic centering and spacing
- Professional borders and padding

## Using the Style Package

### Basic Setup

1. **Add to document preamble:**

```latex
% !TEX program = xelatex
\documentclass[11pt,letterpaper]{article}

% Use custom medical treatment plan style
\usepackage{medical_treatment_plan}
\usepackage{natbib}

\begin{document}
\maketitle
% Your content here
\end{document}
```

2. **Ensure style file is in same directory** as your `.tex` file, or install to LaTeX path

3. **Compile with XeLaTeX** (recommended for best results):

```bash
xelatex treatment_plan.tex
bibtex treatment_plan
xelatex treatment_plan.tex
xelatex treatment_plan.tex
```

### Custom Title Page

The package automatically formats the title with a professional blue header:

```latex
\title{\textbf{Individualized Diabetes Treatment Plan}\\
\large{23-Year-Old Male Patient with Type 2 Diabetes}}
\author{Comprehensive Care Plan}
\date{\today}

\begin{document}
\maketitle
```

This creates an eye-catching blue box with white text and clear hierarchy.

## Compilation Requirements

**Required LaTeX Packages** (automatically loaded by the style):
- `geometry` - Page layout and margins
- `xcolor` - Color support
- `tcolorbox` with `[most]` library - Custom colored boxes
- `tikz` - Graphics and drawing
- `fontspec` - Font management (XeLaTeX/LuaLaTeX)
- `fancyhdr` - Custom headers and footers
- `titlesec` - Section styling
- `enumitem` - Enhanced list formatting
- `booktabs` - Professional table rules
- `longtable` - Multi-page tables
- `array` - Enhanced table features
- `colortbl` - Colored table cells
- `hyperref` - Hyperlinks and PDF metadata
- `natbib` - Bibliography management

**Recommended Compilation:**

```bash
# Using XeLaTeX (best font support)
xelatex document.tex
bibtex document
xelatex document.tex
xelatex document.tex

# Using PDFLaTeX (alternative)
pdflatex document.tex
bibtex document
pdflatex document.tex
pdflatex document.tex
```

## Customization Options

### Changing Colors

Edit the style file to modify the color scheme:

```latex
% In medical_treatment_plan.sty
\definecolor{primaryblue}{RGB}{0, 102, 153}      % Modify these
\definecolor{secondaryblue}{RGB}{102, 178, 204}
\definecolor{accentblue}{RGB}{0, 153, 204}
\definecolor{successgreen}{RGB}{0, 153, 76}
\definecolor{warningred}{RGB}{204, 0, 0}
```

### Adjusting Page Layout

Modify geometry settings in the style file:

```latex
\RequirePackage[margin=1in, top=1.2in, bottom=1.2in]{geometry}
```

### Custom Fonts (XeLaTeX only)

Uncomment and modify in the style file:

```latex
\setmainfont{Your Preferred Font}
\setsansfont{Your Sans-Serif Font}
```

### Header/Footer Customization

Modify in the style file:

```latex
\fancyhead[L]{\color{primaryblue}\sffamily\small\textbf{Treatment Plan Title}}
\fancyhead[R]{\color{darkgray}\sffamily\small Patient Info}
```

## Style Package Download and Installation

### Option 1: Copy to Project Directory

Copy `assets/medical_treatment_plan.sty` to the same directory as your `.tex` file.

### Option 2: Install to User TeX Directory

```bash
# Find your local texmf directory
kpsewhich -var-value TEXMFHOME

# Copy to appropriate location (usually ~/texmf/tex/latex/)
mkdir -p ~/texmf/tex/latex/medical_treatment_plan
cp assets/medical_treatment_plan.sty ~/texmf/tex/latex/medical_treatment_plan/

# Update TeX file database
texhash ~/texmf
```

### Option 3: System-Wide Installation

```bash
# Copy to system texmf directory (requires sudo)
sudo cp assets/medical_treatment_plan.sty /usr/local/texlive/texmf-local/tex/latex/
sudo texhash
```

## Additional Professional Styles (Optional)

Other medical/clinical document styles available from CTAN:

**Journal Styles:**
```bash
# Install via TeX Live Manager
tlmgr install nejm        # New England Journal of Medicine
tlmgr install jama        # JAMA style
tlmgr install bmj         # British Medical Journal
```

**General Professional Styles:**
```bash
tlmgr install apa7        # APA 7th edition (health sciences)
tlmgr install IEEEtran    # IEEE (medical devices/engineering)
tlmgr install springer    # Springer journals
```

**Download from CTAN:**
- Visit: https://ctan.org/
- Search for medical document classes
- Download and install per package instructions

## Troubleshooting

**Issue: Package not found**
```bash
# Install missing packages via TeX Live Manager
sudo tlmgr update --self
sudo tlmgr install tcolorbox tikz pgf
```

**Issue: Missing characters (✓, ≥, etc.)**
- Use XeLaTeX instead of PDFLaTeX
- Or replace with LaTeX commands: `$\checkmark$`, `$\geq$`
- Requires `amssymb` package for math symbols

**Issue: Header height warnings**
- Style file sets `\setlength{\headheight}{22pt}`
- Adjust if needed for your content

**Issue: Boxes not rendering**
```bash
# Ensure complete tcolorbox installation
sudo tlmgr install tcolorbox tikz pgf
```

**Issue: Font not found (XeLaTeX)**
- Comment out custom font lines in .sty file
- Or install specified fonts on your system

## Best Practices for Styled Documents

1. **Appropriate Box Usage**
   - Match box type to content purpose (goals→green, warnings→yellow/red)
   - Don't overuse boxes; reserve for truly important information
   - Keep box content concise and focused

2. **Visual Hierarchy**
   - Use section styling for structure
   - Boxes for emphasis and organization
   - Tables for comparative data
   - Lists for sequential or grouped items

3. **Color Consistency**
   - Stick to defined color scheme
   - Use `\textcolor{primaryblue}{\textbf{Text}}` for emphasis
   - Maintain consistent meaning (red=warning, green=goals)

4. **White Space**
   - Don't overcrowd pages with boxes
   - Use `\vspace{0.5cm}` between major sections
   - Allow breathing room around colored elements

5. **Professional Appearance**
   - Maintain readability as top priority
   - Ensure sufficient contrast for accessibility
   - Test print output in grayscale
   - Keep styling consistent throughout document

6. **Table Formatting**
   - Use `\tableheadercolor` for all header rows
   - Apply `\tablerowcolor` to alternating rows in tables >3 rows
   - Keep column widths balanced
   - Use `\small\sffamily` for large tables

## Example: Styled Treatment Plan Structure

```latex
% !TEX program = xelatex
\documentclass[11pt,letterpaper]{article}
\usepackage{medical_treatment_plan}
\usepackage{natbib}

\title{\textbf{Comprehensive Treatment Plan}\\
\large{Patient-Centered Care Strategy}}
\author{Multidisciplinary Care Team}
\date{\today}

\begin{document}
\maketitle

\section*{Patient Information}
\begin{patientinfo}
  % Demographics table
\end{patientinfo}

\section{Executive Summary}
\begin{keybox}[Plan Overview]
  % Key highlights
\end{keybox}

\section{Treatment Goals}
\begin{goalbox}[SMART Goals - 3 Months]
  \begin{medtable}{Primary Treatment Targets}
    % Goals table with colored headers
  \end{medtable}
\end{goalbox}

\section{Medication Plan}
\begin{infobox}[Titration Schedule]
  % Medication instructions
\end{infobox}

\begin{warningbox}[Critical Decision Point]
  % Important safety information
\end{warningbox}

\section{Emergency Protocols}
\begin{emergencybox}
  % Emergency contacts
\end{emergencybox}

\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
```

## Benefits of Professional Styling

**Clinical Practice:**
- Faster information scanning during patient encounters
- Clear visual hierarchy for critical vs. routine information
- Professional appearance suitable for patient-facing documents
- Color-coded sections reduce cognitive load

**Educational Use:**
- Enhanced readability for teaching materials
- Visual differentiation of concept types (goals, warnings, procedures)
- Professional presentation for case discussions
- Print and digital-ready formats

**Documentation Quality:**
- Modern, polished appearance
- Maintains clinical accuracy while improving aesthetics
- Standardized formatting across treatment plans
- Easy to customize for institutional branding

**Patient Engagement:**
- More approachable than dense text documents
- Color coding helps patients identify key sections
- Professional appearance builds trust
- Clear organization facilitates understanding
