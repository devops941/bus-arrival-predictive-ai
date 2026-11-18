# Wireframe 01: Login & Authentication Screen

**Layout:** Split Screen (50/50 Desktop, Stacks vertically on Mobile)  
**Theme:** Light (`bg-base: #F6F8FB`, `surface: #FFFFFF`)

```
+------------------------------------------+------------------------------------------+
|  LEFT PANEL: Brand & Value (Gradient)    |  RIGHT PANEL: Authentication Card        |
|  (#EAF1FF -> #F6F8FB)                    |  (White #FFFFFF, Shadow, Radius 12px)    |
|                                          |                                          |
|  [Logo] BusArrival AI                    |               Welcome Back               |
|                                          |     Sign in to your transit workspace    |
|  "Know when your bus arrives."           |                                          |
|                                          |  +------------------------------------+  |
|  Subtle transit route SVG background:    |  | Work Email                         |  |
|  o---o========o--------o                 |  | [ user@transit-authority.org     ] |  |
|      \        /                          |  +------------------------------------+  |
|       o======o                           |                                          |
|                                          |  +------------------------------------+  |
|  Key Capabilities:                       |  | Password                 [Show]    |  |
|                                          |  | [ ******************             ] |  |
|  [*] High Precision ML Arrival ETAs      |  +------------------------------------+  |
|      Confidence bands (P50 & P90)        |                                          |
|                                          |  [X] Remember me     [Forgot password?]  |
|  [*] Real-time Bottleneck Insights       |                                          |
|      Per-stop, per-hour delay analysis   |  +------------------------------------+  |
|                                          |  | [>] Sign In (Primary #1D4ED8)      |  |
|  [*] Operational Data Management         |  +------------------------------------+  |
|      Live CRUD tables & CSV validation   |                                          |
|                                          |  ----------------- OR -----------------  |
|                                          |                                          |
|  Role Access:                            |  Don't have an account? [Create Account] |
|  - Passenger: Realtime ETA predictions   |                                          |
|  - Analyst: Models, datasets & reports   |  [Notice: Default admin bootstrap       |
|  - Admin: System & user management       |   available via scripts/create_admin.py] |
+------------------------------------------+------------------------------------------+
```

### Component Details
- **Email/Password inputs:** `#EDF1F7` background on idle, white on focus with `#1D4ED8` focus ring.
- **Show/Hide password toggle:** Accessible button inside password input field.
- **Error message container:** Displays inline validation errors (e.g., "Account locked after 5 failed attempts. Please try again in 15 minutes.").
- **Responsive behavior:** On mobile screens (<768px), the left brand panel collapses into a compact top banner with logo and tagline.
