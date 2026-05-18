You are an expert frontend developer and UI/UX designer. Build a complete, production-ready Next.js 14 web application for the Bibliotheca Alexandrina Antiquities Museum chatbot system. This is a graduation project UI.

---

## AESTHETIC DIRECTION

**Theme:** Ancient Egypt meets modern luxury — dark backgrounds with gold accents, hieroglyphic-inspired decorative elements, papyrus textures subtly in backgrounds. Think "museum at night" — deep navy/black with warm gold, amber, and sand tones.

**Feel:** Premium, cinematic, immersive. Every screen transition should feel like walking through museum halls.

**Fonts:**
- Display/Headers: `Cinzel` (Google Font) — Roman-inspired, fits museum perfectly
- Arabic text: `Noto Naskh Arabic` (Google Font)
- Body: `Cormorant Garamond` — elegant serif

**Colors (CSS variables):**
```css
--bg-primary: #0a0a0f;
--bg-secondary: #12111a;
--bg-card: #1a1825;
--gold: #c9a84c;
--gold-light: #e8c97a;
--gold-dim: #8a6f2e;
--sand: #d4b896;
--text-primary: #f0e6d3;
--text-secondary: #9a8a7a;
--accent-teal: #2a6b6b;
--border: rgba(201, 168, 76, 0.2);
```

---

## TECH STACK (STRICT)

```
Next.js 14 (App Router)
TypeScript
Tailwind CSS
Framer Motion         ← all page transitions + animations
shadcn/ui             ← base components
Zustand               ← global state (language, selected section)
next-intl             ← Arabic/English i18n
React Query           ← API data fetching + caching
Lucide React          ← icons
```

---

## PROJECT STRUCTURE

```
museum-ui/
├── app/
│   ├── layout.tsx                  # Root layout, fonts, providers
│   ├── page.tsx                    # Redirects to /welcome
│   ├── [locale]/
│   │   ├── layout.tsx              # Locale layout with direction (RTL/LTR)
│   │   ├── welcome/
│   │   │   └── page.tsx            # Screen 1: Welcome + language picker
│   │   ├── sections/
│   │   │   └── page.tsx            # Screen 2: Sections grid
│   │   ├── sections/[sectionId]/
│   │   │   └── page.tsx            # Screen 3: Artifacts in section
│   │   └── artifacts/[artifactId]/
│   │       └── page.tsx            # Screen 4: Artifact detail + chat
│
├── components/
│   ├── ui/                         # shadcn components
│   ├── layout/
│   │   ├── FloatingAIButton.tsx    # Persistent AI chat button
│   │   └── PageTransition.tsx      # Framer Motion page wrapper
│   ├── welcome/
│   │   ├── WelcomeHero.tsx
│   │   └── LanguageSelector.tsx
│   ├── sections/
│   │   ├── SectionCard.tsx
│   │   └── SectionsGrid.tsx
│   ├── artifacts/
│   │   ├── ArtifactCard.tsx
│   │   ├── ArtifactsGrid.tsx
│   │   └── SearchBar.tsx
│   └── artifact-detail/
│       ├── ArtifactHero.tsx
│       ├── ArtifactInfo.tsx
│       ├── QuickQuestions.tsx
│       └── ChatPanel.tsx
│
├── lib/
│   ├── api.ts                      # FastAPI client functions
│   ├── store.ts                    # Zustand store
│   └── utils.ts
│
├── messages/
│   ├── en.json                     # English strings
│   └── ar.json                     # Arabic strings
│
├── hooks/
│   ├── useArtifacts.ts
│   ├── useSections.ts
│   └── useChat.ts
│
└── types/
    └── index.ts                    # TypeScript interfaces
```

---

## SCREEN 1 — Welcome Page (`/[locale]/welcome`)

### Layout
Full viewport height. Background: deep dark with subtle animated golden particles floating upward (CSS keyframe animation, 20-30 small golden dots).

### Content (centered, vertical stack)
1. **Top:** Small decorative horizontal line with diamond shape in center (pure CSS, gold color)
2. **Museum logo area:** Stylized eye of Horus SVG icon (inline SVG, gold colored) — 80px
3. **Main title:** "BIBLIOTHECA ALEXANDRINA" in Cinzel font, letter-spacing wide, gold color, large (48px desktop)
4. **Subtitle:** "Antiquities Museum" smaller, sand color
5. **Decorative divider:** thin gold line with small hieroglyphic-style decorations on sides
6. **Language prompt text:** "Choose your language / اختر لغتك" — both on same line, text-secondary color
7. **Two language buttons** side by side:
   - Left: "English" button
   - Right: "عربي" button
   - Style: bordered cards, not filled. On hover: gold border glows, background subtly fills with gold at 10% opacity. Each has a small flag emoji or language icon.
8. **Bottom:** Small text "Bibliotheca Alexandrina © 2024"

### Behavior
- Clicking a language button sets locale + saves to Zustand store + navigates to `/[locale]/sections`
- Entry animation: staggered fade-in from bottom, each element 100ms delay after previous

---

## SCREEN 2 — Sections Page (`/[locale]/sections`)

### Layout
- **Header bar** (sticky): Museum name small on left, current language + switch button on right, thin gold bottom border
- **Page title section:** "Our Collections" / "مجموعاتنا" — centered, large Cinzel font, with decorative underline
- **Sections grid:** 2 columns on mobile, 3 on tablet, 3-4 on desktop

### Section Card Design
Each card is a rich visual card:
- Background: dark card color with subtle gradient
- **Top half:** Large icon area — use a unique SVG icon per section type (Ancient Egyptian → ankh, Greco-Roman → column, Islamic → crescent, etc.)
- **Gold top border:** 3px gold line at very top of card
- **Section name** in Cinzel, gold color
- **Arabic section name** below in smaller Noto Naskh Arabic
- **Artifact count badge:** small pill badge bottom right "12 artifacts"
- **Hover effect:** card lifts (translateY -4px), gold border glows with box-shadow, icon subtly scales up

### Sections data (hardcode these based on the CSV data):
```javascript
const sections = [
  { id: 38, nameEn: "Ancient Egyptian Antiquities", nameAr: "الآثار المصرية القديمة", icon: "ankh", count: 60 },
  { id: 39, nameEn: "Greco-Roman Antiquities", nameAr: "الآثار اليونانية والرومانية", icon: "column", count: 20 },
  { id: 40, nameEn: "Islamic Antiquities", nameAr: "الآثار الإسلامية", icon: "crescent", count: 10 },
  { id: 41, nameEn: "Coins Collection", nameAr: "مجموعة العملات", icon: "coin", count: 7 },
]
```

### Floating AI Button
- Fixed position, bottom-right corner
- Circle button, gold gradient background
- Sparkles/wand icon inside
- Subtle pulse animation (scale 1 → 1.05 → 1, loop)
- Tooltip on hover: "Ask AI Guide" / "اسأل المرشد الذكي"
- On click: opens a slide-up panel (drawer) with full chat interface connected to `/chat` API

---

## SCREEN 3 — Artifacts Page (`/[locale]/sections/[sectionId]`)

### Layout
- **Back button** top left: "← Collections" / "← المجموعات" with arrow, navigates back
- **Section hero:** Section name large + section icon, centered, with decorative gold border below
- **Search bar:** centered below hero, full width on mobile, 60% on desktop
  - Placeholder: "Search artifacts..." / "ابحث عن قطعة..."
  - Gold focus ring
  - Search icon inside
- **Artifacts grid:** 2 cols mobile, 3 tablet, 4 desktop

### Artifact Card Design
- **Image area:** top 60% of card — use the artifact's image from the BibaAlex URL, fallback to a placeholder with hieroglyphic pattern SVG if image fails
- **Bottom 40%:** dark background
  - Artifact name in Cinzel (English or Arabic based on locale)
  - Hall name — smaller, text-secondary
  - Small "View Details →" text that appears on hover
- **Hover:** image zooms slightly (scale 1.05), overlay appears with 20% dark tint

### Data fetching
Call `GET /artifacts?section={sectionId}` from the FastAPI backend.

### Floating AI Button — same as Screen 2

---

## SCREEN 4 — Artifact Detail Page (`/[locale]/artifacts/[artifactId]`)

### Layout
Two-column on desktop (60/40 split), single column on mobile.

**Left column (60%):**

1. **Back button:** "← Back" / "← رجوع" — absolute top left
2. **Artifact image:** Large, with subtle gold border frame, rounded corners. If image unavailable: decorative placeholder with papyrus texture effect (CSS background)
3. **Artifact title:** Large Cinzel font, gold color
4. **Arabic title:** below, Noto Naskh Arabic, smaller
5. **Metadata pills row:**
   - 🏛️ Hall name
   - 📍 Discovery site
   - 🏷️ Category
   - Each pill: dark background, gold border, small text
6. **Description:** Full text in Cormorant Garamond, text-primary, line-height 1.8, scrollable if long
7. **External link:** "View on BibaAlex →" — links to artifact URL, small gold text

**Right column (40%) — Chat Panel:**

1. **Panel header:** "Ask About This Artifact" / "اسأل عن هذه القطعة" with AI sparkle icon
2. **Quick Questions section:**
   - Label: "Quick questions:" / "أسئلة سريعة:"
   - 3-4 pill buttons with preset questions:
     - "When was it discovered?" / "متى اكتشفت؟"
     - "What is it made of?" / "من ماذا صُنعت؟"
     - "What is its historical significance?" / "ما أهميتها التاريخية؟"
     - "Tell me more about [artifact name]" / "أخبرني أكثر"
   - Clicking a quick question sends it immediately to chat
3. **Chat messages area:**
   - Scrollable list of messages
   - User messages: right-aligned, gold background, dark text
   - AI messages: left-aligned, dark card background, gold-tinted border on left side (3px), text-primary
   - AI messages show "Alex 🤖" / "إسكندر 🤖" as sender name
   - Loading state: animated dots (three dots pulsing)
4. **Input area (bottom):**
   - Text input + send button
   - Microphone button for voice input (calls `/voice` endpoint)
   - Recording state: mic button turns red, pulses
   - Send button: gold background, arrow icon

### Chat behavior
- First message auto-sent: "Tell me about [artifact name]" when page loads — gives immediate context
- Maintains conversation history in component state (not persisted)
- Calls `POST /chat` with `{ query: string, artifact_context: { name, description_preview } }`
- Voice: records audio → sends to `POST /voice` → receives MP3 → auto-plays response audio

---

## GLOBAL COMPONENTS

### FloatingAIButton (`components/layout/FloatingAIButton.tsx`)
- Always visible on Screens 2, 3, 4
- Opens a full general chat drawer (slide up from bottom, 60vh height)
- This chat has no artifact context — general museum questions
- Same design as the artifact chat panel but in a drawer

### PageTransition (`components/layout/PageTransition.tsx`)
Wrap every page with Framer Motion:
```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.4, ease: "easeInOut" }}
>
  {children}
</motion.div>
```

---

## INTERNATIONALIZATION

`messages/en.json`:
```json
{
  "welcome": {
    "title": "BIBLIOTHECA ALEXANDRINA",
    "subtitle": "Antiquities Museum",
    "chooseLanguage": "Choose your language",
    "english": "English",
    "arabic": "عربي"
  },
  "sections": {
    "title": "Our Collections",
    "artifactCount": "{count} artifacts"
  },
  "artifacts": {
    "searchPlaceholder": "Search artifacts...",
    "viewDetails": "View Details",
    "backToCollections": "← Collections"
  },
  "detail": {
    "askAbout": "Ask About This Artifact",
    "quickQuestions": "Quick questions:",
    "q1": "When was it discovered?",
    "q2": "What is it made of?",
    "q3": "What is its historical significance?",
    "q4": "Tell me more",
    "inputPlaceholder": "Ask anything...",
    "viewOnBibaAlex": "View on BibaAlex →",
    "back": "← Back"
  },
  "ai": {
    "senderName": "Alex",
    "floatingTooltip": "Ask AI Guide",
    "thinking": "Thinking..."
  }
}
```

`messages/ar.json` — same keys, Arabic values, direction RTL.

---

## API INTEGRATION (`lib/api.ts`)

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export async function getArtifacts(sectionId?: number, search?: string) {
  const params = new URLSearchParams()
  if (sectionId) params.append("section", sectionId.toString())
  if (search) params.append("q", search)
  const res = await fetch(`${API_BASE}/artifacts?${params}`)
  return res.json()
}

export async function getArtifact(id: string) {
  const res = await fetch(`${API_BASE}/artifacts/${id}`)
  return res.json()
}

export async function sendChatMessage(query: string, artifactContext?: object) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, artifact_context: artifactContext })
  })
  return res.json()
}

export async function sendVoiceMessage(audioBlob: Blob) {
  const formData = new FormData()
  formData.append("audio", audioBlob, "recording.webm")
  const res = await fetch(`${API_BASE}/voice`, {
    method: "POST",
    body: formData
  })
  return res.blob() // returns MP3
}
```

---

## ZUSTAND STORE (`lib/store.ts`)

```typescript
interface MuseumStore {
  language: "en" | "ar"
  selectedSection: number | null
  setLanguage: (lang: "en" | "ar") => void
  setSelectedSection: (id: number) => void
}
```

---

## TYPES (`types/index.ts`)

```typescript
interface Artifact {
  id: string
  section_number: number
  section_name_en: string
  section_name_ar: string
  artifact_name_en: string
  artifact_name_ar: string
  description_en: string
  description_ar: string
  category_en: string
  category_ar: string
  discovery_site_en: string
  discovery_site_ar: string
  hall_en: string
  hall_ar: string
  link: string
  image_url?: string
}

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

interface Section {
  id: number
  nameEn: string
  nameAr: string
  icon: string
  count: number
}
```

---

## ENVIRONMENT VARIABLES

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ADDITIONAL DESIGN DETAILS

1. **Scrollbar styling:** Custom thin gold scrollbar on webkit browsers
2. **Selection color:** Gold background when user selects text
3. **Focus rings:** Gold color throughout (`outline-color: var(--gold)`)
4. **Loading states:** Skeleton cards with shimmer animation (dark base, lighter shimmer moving left to right)
5. **Error states:** Subtle red-tinted card with message, no full-page errors
6. **Empty states:** Illustrated empty state with small hieroglyphic SVG and helpful message
7. **RTL support:** When Arabic locale, entire layout flips (flexbox direction, text align, padding/margin mirror) — use `dir="rtl"` on html element
8. **Image optimization:** Use Next.js `<Image>` component with `unoptimized` for external BibaAlex URLs

---

## DELIVERABLES

Generate ALL files completely:
1. `app/layout.tsx` and `app/[locale]/layout.tsx`
2. All 4 page files
3. All components listed in the structure
4. `lib/api.ts`, `lib/store.ts`, `lib/utils.ts`
5. `messages/en.json` and `messages/ar.json`
6. `hooks/useArtifacts.ts`, `hooks/useSections.ts`, `hooks/useChat.ts`
7. `types/index.ts`
8. `tailwind.config.ts` with custom colors and fonts
9. `next.config.ts` with i18n and image domains config
10. `package.json` with all dependencies
11. `README.md` with setup instructions

Do not skip any file. Implement fully. No placeholder comments. The UI must be visually stunning — dark museum aesthetic with gold accents, smooth Framer Motion transitions, fully bilingual AR/EN.
