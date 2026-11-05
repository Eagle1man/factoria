# Stripe Press — Style Reference
> cloth-bound spines in a lamplit study. Float richly printed books over a dark umber field and let quiet literary serif type do the rest.

**Theme:** dark

Source measurements are normalized; roles and recommendations are interpreted. Font summary lists are independent, not paired by position. HTML examples are reconstructions, not source components.

Stripe Press is a publisher's catalogue staged as a three-dimensional bookshelf: lit book models stack and turn on a full-bleed Bindery Umber #201819 field while the interface itself nearly disappears. The only chrome above the books is a small Paper #ffffff wordmark with an italic tagline and a left rail of index ticks, so all colour lives in the covers: marbled teal, ochre, kintsugi gold, saturated reds. Ivar Headline at 600 and Ivar Text at 500, both carrying a faint +0.32px tracking on labels, give every line a book-jacket voice. The page closes on a plain white colophon of 25px serif prose, a square Proof Wash #eeeeee field beside a Press Charcoal #222222 Submit button, and an italic address.

## Colors

| Name | Value | Role |
|------|-------|------|
| Bindery Umber | `#201819` | Full-bleed stage behind the floating book stack and header — a red-tinged near-black that reads as dark cloth binding, not screen black |
| Paper | `#ffffff` | Wordmark, monogram strokes and index ticks on Bindery Umber, then the whole colophon footer canvas |
| Ink | `#000000` | Colophon prose, underlined links, social glyphs and input text on the white footer |
| Press Charcoal | `#222222` | Square Submit button fill and the dark film backdrop behind the Beneath the Surface series |
| Proof Wash | `#eeeeee` | Email field fill, measured as rgba(0, 0, 0, 0.067) over Paper — a faint grey proof-sheet tint instead of a border |
| Rule Gray | `#bfbfbf` | The single 1px rgba(0, 0, 0, 0.25) hairline separating the colophon prose from the legal and address row |

## Typography

### Ivar Text — The reading face for everything set as prose: 25px/500 colophon statements at 1.5, the 18px/500 newsletter prompt, and 14px/500 legal copy and underlined links at 19.6px line-height. Held at medium 500 rather than regular, it reads like a well-inked book page; links alone take +0.32px tracking.
- **Substitute:** Source Serif 4, Georgia, serif
- **Licence:** commercial; buy a licence from its foundry, or use the substitute
- **Weights:** 500
- **Sizes:** 14px, 18px, 25px
- **Line height:** 1.40, 1.50
- **Letter spacing:** +0.32px at 14px on links; 0px at 14px, 18px and 25px prose

### Ivar Headline — The imprint's label face: the 17.6px/600 Stripe Press wordmark at 1.0 line-height, the italic 16px/600 Ideas for progress tagline at 1.3, and the 17px/600 Submit label. Small, semibold and lightly tracked at +0.32px, it behaves like a title-page imprint rather than a marketing headline; no large display sizes exist in the DOM.
- **Substitute:** Source Serif 4, Georgia, serif
- **Licence:** commercial; buy a licence from its foundry, or use the substitute
- **Weights:** 600
- **Sizes:** 16px, 17px, 17.6px
- **Line height:** 1.00, 1.30
- **Letter spacing:** +0.32px at 16px, 17px and 17.6px

### Georgia — Renders only inside the newsletter email field at 17px/400 with normal line-height and tracking, because the input does not inherit Ivar. It is close enough in colour to the surrounding serif that the field still feels typeset.
- **Substitute:** Times New Roman, serif
- **Weights:** 400
- **Sizes:** 17px
- **Line height:** 

### Type Scale

| Role | Family | Weight | Size | Line Height | Letter Spacing |
|------|--------|--------|------|-------------|----------------|
| legal | Ivar Text | 500 | 14px | 1.4 | 0px |
| link | Ivar Text | 500 | 14px | 1.4 | 0.32px |
| tagline | Ivar Headline | 600 | 16px | 1.3 | 0.32px |
| wordmark | Ivar Headline | 600 | 17.6px | 1 | 0.32px |
| prompt | Ivar Text | 500 | 18px | 1.5 | 0px |
| statement | Ivar Text | 500 | 25px | 1.5 | 0px |

## Spacing & Layout

**Base unit:** 4px

**Density:** spacious

- **Section gap:** 100px
- **Card padding:** 26px
- **Element gap:** 20px

### Border Radius

- **buttons:** 0px
- **inputs:** 0px
- **footer:** 2px

## Components

### Imprint Header Bar
**Role:** Wordmark and tagline over the dark stage

A 44px transparent bar over Bindery Umber #201819 with no border or shadow: a white outline coil monogram at left, then a Paper #ffffff Ivar Headline 17.6px/600 wordmark at 1.0 line-height and +0.32px tracking above an italic 16px/600 tagline at 20.8px line-height.

### Floating Book Stack
**Role:** Signature 3D catalogue of titles

Centre a canvas-rendered stack of lit book models, about half the viewport wide, on Bindery Umber #201819; spines face the viewer with author at left, title centred and monogram at right, and scroll advances and rotates the stack. No DOM card, 0px border, no CSS shadow.

### Spine Index Rail
**Role:** Vertical book index and progress

A column of short Paper #ffffff tick marks about 30px from the left edge, one per title, with the active tick drawn longer; each is a transparent 0px-radius button with 2px top padding and an Ivar Headline 15px/600 +0.32px label, followed by video and podcast glyphs.

### Film Series Panel
**Role:** Video series feature inside the stage

A full-bleed Press Charcoal #222222 backdrop carrying an autoplaying film with its own title card and caption baked into the media; add no DOM headline, border, radius or shadow over it, and let it scroll in after the last book.

### Colophon Statement Block
**Role:** About-the-imprint prose

On Paper #ffffff, inset 224px from the left in a roughly 850px column, set Ink #000000 Ivar Text 25px/500 at 37.5px line-height with 0px tracking; separate paragraphs by one blank line and add no heading above them.

### Proof Wash Email Field
**Role:** Newsletter address input

A 460px by 49px field filled with Proof Wash #eeeeee (rgba(0, 0, 0, 0.067)), no border, 0px radius and 1px 2px 1px 8px padding; text in Georgia 17px/400 Ink #000000 with a grey placeholder, preceded by an Ivar Text 18px/500 prompt at 27px line-height.

### Press Charcoal Submit Button
**Role:** Newsletter submit control

Fill Press Charcoal #222222 with a Paper #ffffff Ivar Headline 17px/600 label at +0.32px tracking, 14px 40px padding, 49px height, 0px radius, no border and no shadow; butt it directly against the right edge of the email field.

### Underlined Serif Link
**Role:** Inline legal and contact links

Ink #000000 Ivar Text 14px/500 at 19.6px line-height and +0.32px tracking with a plain underline, transparent background and 0px padding; used inside legal sentences and for the contact email.

### Colophon Footer
**Role:** Legal, address and social row

A Paper #ffffff footer with 26px top padding and a 2px radius; a 1px Rule Gray #bfbfbf hairline spans the 224px-inset column above Ivar Text 14px/500 legal copy at left and an italic right-aligned address, with Ink social glyphs and a back-to-top arrow above.

## Do's and Don'ts

### Do
- Use Bindery Umber #201819 as the full-bleed catalogue canvas; it is warmer and redder than pure black.
- Set the wordmark in Ivar Headline 17.6px/600 at 1.0 line-height with +0.32px tracking, and the italic tagline at 16px/600 directly beneath.
- Set colophon prose in Ivar Text 25px/500 at 37.5px line-height with 0px tracking, Ink #000000 on Paper #ffffff.
- Keep every DOM control square: 0px radius on the Submit button and email field, 2px only on the footer container.
- Pair a 49px-high Proof Wash #eeeeee email field with a Press Charcoal #222222 Submit button at 14px 40px padding, butted together with no gap.
- Let the book covers carry all of the page's colour; limit the interface to Bindery Umber, Paper, Ink and Press Charcoal.
- Apply transform and opacity transitions at 0.2s or 0.3s with plain ease, and +0.32px tracking on Ivar Headline labels and 14px links.

### Don't
- Do not borrow the parent Stripe gradients or a blurple accent; this imprint's interface has no accent colour beyond Paper and Ink.
- Do not switch buttons or labels to a sans-serif; the Submit label is Ivar Headline 17px/600 and links are Ivar Text 14px/500.
- Do not round buttons or inputs into pills or soft cards; keep them at 0px radius.
- Do not add drop shadows to DOM elements; depth belongs to the rendered 3D books, and the DOM has no shadow at all.
- Do not reach for bold 700 headline weights; Ivar Text stays at 500 and Ivar Headline at 600, even for the 25px statement.
- Do not lay the books out as a flat grid of rounded cover cards; present them as lit spines stacked in perspective on Bindery Umber #201819.
- Do not crowd the dark stage with headlines or paragraphs; the 44px header and the index rail are the only DOM type over the books.

## Elevation

The DOM is completely flat: no box-shadows were measured, controls are square, and the only line is one 1px Rule Gray hairline in the footer. All depth is real 3D on the canvas, where lit book models with visible spines, page edges and soft shading float in perspective over Bindery Umber. Separation in the footer comes from tonal fills (Proof Wash field, Press Charcoal button) rather than borders or elevation.

## Surfaces

- **Bindery Umber** (`#201819`) — The dark catalogue stage behind the header, rail and book stack.
- **Press Charcoal** (`#222222`) — Film backdrop for the Beneath the Surface series section.
- **Paper** (`#ffffff`) — The white colophon footer with statement, newsletter and legal.
- **Proof Wash** (`#eeeeee`) — Email field fill set into the Paper footer.

## Imagery

The books are the imagery. High-resolution cover and spine artwork (marbled endpaper swirls, engraved diagrams, cartographic linework with gold kintsugi cracks, bold slab titling, saturated reds, blues and ochres) is mapped onto lit 3D book models with visible page edges and soft shading, rendered on a canvas over Bindery Umber. Each spine repeats the same anatomy: author at left, title centred, coiled monogram at right. Series sections swap in atmospheric media instead: a starfield background image behind We Are As Gods and a full-bleed film with a large title card for Beneath the Surface. There is no people photography and no product UI. Iconography is minimal outline work: the coiled S monogram, Twitter and Instagram glyphs, a back-to-top arrow, and index ticks.

## Layout

The 7362px page is two acts. The first ~6275px is one dark Bindery Umber stage: a 44px transparent header pins the monogram and two-line wordmark to the top-left corner, a vertical rail of short Paper index ticks sits about 30px from the left edge at mid-height with video and podcast glyphs below it, and a lone ? help glyph sits bottom-left. Everything else is a WebGL canvas: a centred stack of book models, roughly half the viewport wide with four spines in view, that advances and rotates as you scroll, followed by a Press Charcoal film section for the Beneath the Surface series. The second act is the white colophon: a back-to-top arrow at top-left, content inset 224px from the left, a roughly 850px column of 25px serif statement paragraphs, 100px of air, a newsletter row, Ink social glyphs, then a hairline-ruled legal row with italic address right-aligned at 1376px. Density is spacious and almost wordless.

## Similar Brands

- **Works in Progress** — Shares a literary serif voice and essay-first presentation of ideas about progress with almost no interface decoration.
- **The Paris Review** — Uses classic book-face serif typography and a restrained, print-derived page that defers to the writing and cover art.
- **Kinfolk** — Same generous editorial whitespace and quiet serif typesetting with colour supplied by the imagery rather than the interface.
- **Igloo Inc** — Shares a scroll-driven WebGL stage where 3D objects, not DOM sections, carry the narrative of the page.
