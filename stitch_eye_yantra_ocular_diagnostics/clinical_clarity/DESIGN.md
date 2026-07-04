---
name: Clinical Clarity
colors:
  surface: '#fbf8ff'
  surface-dim: '#dbd9df'
  surface-bright: '#fbf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2f9'
  surface-container: '#efedf3'
  surface-container-high: '#e9e7ed'
  surface-container-highest: '#e4e1e8'
  on-surface: '#1b1b20'
  on-surface-variant: '#454650'
  inverse-surface: '#303035'
  inverse-on-surface: '#f2f0f6'
  outline: '#767681'
  outline-variant: '#c6c5d2'
  surface-tint: '#4c5a9d'
  primary: '#001256'
  on-primary: '#ffffff'
  primary-container: '#1b2a6b'
  on-primary-container: '#8694db'
  inverse-primary: '#b9c3ff'
  secondary: '#006a62'
  on-secondary: '#ffffff'
  secondary-container: '#71f8e8'
  on-secondary-container: '#007168'
  tertiary: '#171b21'
  on-tertiary: '#ffffff'
  tertiary-container: '#2c3036'
  on-tertiary-container: '#94989f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b9c3ff'
  on-primary-fixed: '#001257'
  on-primary-fixed-variant: '#344283'
  secondary-fixed: '#71f8e8'
  secondary-fixed-dim: '#4fdbcc'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#dfe2ea'
  tertiary-fixed-dim: '#c3c6ce'
  on-tertiary-fixed: '#181c21'
  on-tertiary-fixed-variant: '#43474d'
  background: '#fbf8ff'
  on-background: '#1b1b20'
  surface-variant: '#e4e1e8'
typography:
  display-lg:
    fontFamily: Sora
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Sora
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Sora
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Sora
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  code-diagnostic:
    fontFamily: Fira Code
    fontSize: 13px
    fontWeight: '450'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1440px
  gutter: 24px
---

## Brand & Style
The design system for this ocular diagnostics platform is built on the intersection of medical precision and futuristic transparency. The brand personality is authoritative yet approachable, evoking trust through clinical rigor and technological sophistication. 

The design style employs **Glassmorphism** to create a sense of depth and lightness, essential for high-density diagnostic data. By using translucent layers and backdrop blurs, the UI avoids the "heavy" feeling of traditional medical software, replacing it with an airy, high-end laboratory aesthetic. Visuals are crisp, with soft gradients providing a soothing environmental backdrop that reduces eye strain for clinicians during extended use.

## Colors
The palette is rooted in **Deep Indigo**, providing the "Clinical Authority" necessary for diagnostic reliability. **Vibrant Teal** serves as the functional driver, reserved strictly for interactive elements and calls to action. 

The background utilizes a soft, horizontal gradient transitioning from a refreshing Mint to a stable Greyish-Blue. This gradient acts as the canvas for glass-morphic surfaces. Semantic colors (Emerald, Coral, Amber) are utilized for immediate diagnostic feedback, ensuring critical patient data states are identified instantly without competing with the primary brand colors.

## Typography
Typography is layered to balance marketing impact with functional utility. **Sora** is used for headings to convey a modern, geometric confidence. **Inter** handles the bulk of clinical data entry and patient information, chosen for its exceptional legibility and neutral tone.

For specific technical outputs—such as eye-tracking coordinates, diagnostic logs, and machine metadata—**Fira Code** is employed. This monospaced choice ensures that numerical data aligns vertically in tables and logs, allowing clinicians to scan for anomalies across data columns with mathematical precision.

## Layout & Spacing
The design system uses a **12-column fluid grid** for the main dashboard view, with a 24px gutter to maintain "breathing room" between complex diagnostic charts. 

- **Desktop:** 12 columns, 40px side margins.
- **Tablet:** 8 columns, 24px side margins.
- **Mobile:** 4 columns, 16px side margins. 

The vertical rhythm is based on an 8px scale, though a 4px "half-step" is permitted for tight technical UI elements like toolbars and iconography within diagnostic viewports. Content should be grouped in glass containers with generous internal padding (min 24px) to emphasize the premium feel.

## Elevation & Depth
Depth is created through **Glassmorphism** rather than traditional drop shadows. Surfaces are defined by:
- **Backdrop Blur:** A consistent 20px Gaussian blur on the background layer.
- **Surface Fill:** Semi-transparent white (`rgba(255, 255, 255, 0.6)`).
- **Edge Definition:** A 1px solid border with low opacity (`rgba(255, 255, 255, 0.4)`) to simulate the catch-light on the edge of a glass lens.
- **Inner Glow:** Elements in an "active" or "focused" state receive a subtle outer glow using the Teal accent color, suggesting a digital screen or backlit medical device.

## Shapes
The shape language is "Soft-Modern." A standard radius of **12px** is applied to buttons, input fields, and small cards. Larger containers and primary dashboard panels should use **24px (rounded-xl)** to lean into the approachable, premium feel. 

Iconography should follow a "Line" style with rounded terminals to match the font weight of Inter, ensuring a unified visual weight across the interface.

## Components
### Buttons
Primary buttons use the Vibrant Teal fill with white text. Hover states trigger a "glowing" effect (box-shadow with Teal tint). Secondary buttons use the Deep Indigo outline with a glass background.

### Cards
All cards must implement the 20px backdrop blur. For diagnostic cards, the header should be separated by a subtle 1px divider.

### Diagnostic Logs
Presented in Fira Code within a recessed, darker glass container to distinguish machine-generated data from human-readable labels.

### Input Fields
Inputs use a 12px radius and a light glass fill. On focus, the border transitions to Vibrant Teal with a subtle 4px outer glow.

### Status Indicators
Small, high-saturation "pills" or glowing dots. Use Emerald for "Healthy/Normal," Coral for "Pathology Detected," and Amber for "Inconclusive/Action Required."

### Progress Steps
Use a refined horizontal track with Teal "glow" nodes to indicate the stages of an ocular scan or patient intake process.