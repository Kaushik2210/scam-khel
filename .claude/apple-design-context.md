# Apple Design Context

## Product
- **Name**: SCAM-KHEL
- **Description**: Private family shield against Indian "digital arrest" scams: live risk detection, a simulated decoy "confused elder" honeypot, family alerts and complaint drafts.
- **Category**: Safety / utility (Personal AI)
- **Stage**: Development (hackathon build)

## Platforms
| Platform | Supported | Min OS | Notes |
|----------|-----------|--------|-------|
| iOS      | Web only  | n/a    | Mobile-first responsive web app (Next.js), HIG principles translated to web |
| iPadOS   | Web only  | n/a    | Same responsive layout |
| macOS    | Web only  | n/a    | Same responsive layout |
| tvOS / watchOS / visionOS | No | | |

## Technology
- **UI Framework**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS
- **Architecture**: Single-page-style app; WebSocket for live sessions; FastAPI backend
- **Apple Technologies**: none (web). SF Symbols -> inline SVG icon set; Dynamic Type -> rem units; materials -> backdrop-filter with solid fallback

## Design System
- **Base**: HIG-derived tokens (semantic colors via CSS variables, system font stack, 8pt grid)
- **Brand Colors**: none; no third-party/agency logos (hackathon rule). Fictional agencies are always labelled "(SIMULATION)"
- **Typography**: system-ui / -apple-system stack, Apple text-style scale in rem
- **Dark Mode**: Supported, follows `prefers-color-scheme` (dark is the fallback)
- **Dynamic Type**: rem-based; user font-size preference respected

## Accessibility
- **Target Level**: WCAG AA (comprehensive)
- **Key Considerations**: 44px minimum targets (64px in Parent View), visible focus, keyboard operable, live regions for risk changes, `prefers-reduced-motion`, Hindi + English, never rely on colour alone for risk level

## Users
- **Primary Persona**: Elderly Indian user targeted by phone scams (Parent View) and their adult children (Family/Incidents)
- **Key Use Cases**: Check "is this a scam?", watch a simulated honeypot, receive/triage alerts, download a complaint draft, "I already sent money" panic flow
- **Known Challenges**: Low digital literacy, Hindi/Hinglish, high stress; the UI must be calm and unambiguous
