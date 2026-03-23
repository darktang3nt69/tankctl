# TankCtl UI Spec: Dashboard, Events, and Settings Tabs

## Purpose

This document defines the structure and expected behavior for the **Dashboard**, **Events**, and **Settings** tabs in the TankCtl mobile app, with special focus on the **Events** tab.

The goal is to give Copilot enough product and UI direction to generate a solid first implementation.

---

## High-Level Tab Structure

The app should have **3 primary tabs**:

1. **Dashboard**
2. **Events**
3. **Settings**

### 1) Dashboard Tab
The Dashboard is the operational home screen.

**Purpose**
- Show all tanks at a glance
- Surface important live status quickly
- Provide quick actions
- Highlight active warnings or recent issues

**Suggested content**
- Tank cards / tank list
- Current temperature
- Light status
- Device connectivity status
- Last updated timestamp
- Quick controls such as light toggle
- Small "recent events" preview for each tank or globally

**Good additions**
- Active alerts banner at the top
- “Needs attention” section
- Summary chips:
  - Online devices
  - Offline devices
  - Active warnings
  - Recent events count

---

### 2) Events Tab
The Events tab is the historical activity and monitoring view.

**Purpose**
- Show device-related events in a clear timeline or list
- Allow users to filter and inspect important changes
- Help users understand what happened, when it happened, and to which tank/device

This tab is focused on:
- Light toggle events
- Temperature warnings
- Device online/offline events
- Future device/system events

---

### 3) Settings Tab
The Settings tab manages app-level and user-level preferences.

**Purpose**
- Configure notifications
- Manage thresholds
- Control app preferences
- View device/app metadata

**Suggested sections**
- Notification settings
- Event retention preferences
- About app

---

# Events Tab Design

## Main Goal

The Events tab should answer these questions quickly:

- What happened?
- Which tank/device did it happen on?
- When did it happen?
- How important is it?
- Do I need to take action?

---

## Event Types to Support

Initial event types:

1. **Light Toggled**
   - Light turned ON
   - Light turned OFF

2. **Temperature Warnings**
   - High temperature warning
   - Low temperature warning
   - Temperature back to normal

3. **Connectivity Events**
   - Device went online
   - Device went offline
   - Reconnected

4. **System / Sync Events** (recommended)
   - Command sent
   - Command failed
   - Sensor reading missed
   - Device heartbeat missed
   - Configuration updated

---

## Recommended Event Severity Levels

Each event should have a severity or importance level.

- **Info**
  - Light toggled
  - Device online
  - Settings updated

- **Warning**
  - Temperature approaching threshold
  - Device briefly disconnected
  - Delayed sensor update

- **Critical**
  - Temperature out of safe range
  - Device offline for too long
  - Repeated command failures

This helps with:
- color treatment
- icon selection
- filtering
- sorting by importance

---

## Events Tab Layout

## Screen Structure

### Top area
- Page title: **Events**
- Optional subtitle: “Device activity and alerts”

### Filter row
Include a compact filter bar near the top with:
- Event type filter
- Tank filter
- Severity filter
- Date/time filter
- Search input or search icon

### Main content area
- Scrollable event list
- Group by time such as:
  - Today
  - Yesterday
  - Earlier this week
  - Older

### Optional bottom utility
- Clear filters button
- Export / share logs later
- Mark viewed / acknowledge for alerts

---

## Event List Item Design

Each event row/card should show:

- **Event icon**
- **Event title**
- **Short description**
- **Tank name**
- **Device name** if applicable
- **Timestamp**
- **Severity**
- Optional status badge

### Example event entries

#### Example 1
- Title: `Light turned ON`
- Description: `Main light was enabled from app control`
- Tank: `Living Room Tank`
- Time: `Today, 7:15 PM`
- Severity: `Info`

#### Example 2
- Title: `High temperature warning`
- Description: `Water temperature reached 29.8°C`
- Tank: `Betta Tank`
- Time: `Today, 2:04 PM`
- Severity: `Warning`

#### Example 3
- Title: `Device offline`
- Description: `Controller has not reported for 5 minutes`
- Tank: `Shrimp Tank`
- Time: `Yesterday, 11:48 PM`
- Severity: `Critical`

---

## Suggested Filter Options

The Events tab should support filtering by:

### 1) Event Type
- All
- Light
- Temperature
- Connectivity
- System

### 2) Tank
- All tanks
- Specific tank names

### 3) Severity
- All
- Info
- Warning
- Critical

### 4) Time Range
- All time
- Today
- Last 24 hours
- Last 7 days
- Custom range

### 5) Device
Recommended if a tank can have multiple devices:
- All devices
- Controller
- Temperature sensor
- Lighting relay
- Other future devices

### 6) Status / Source
Optional:
- Triggered automatically
- Triggered manually
- App initiated
- Device initiated
- Server initiated

---

## Sorting Options

Recommended sort modes:
- Newest first (default)
- Oldest first
- Severity high to low

---

## Suggested UI Behaviors

### Default state
- Show newest events first
- Filters collapsed or compact
- Most recent critical/warning events visible near top

### Filter behavior
- Filters should update the list immediately
- Active filters should appear as removable chips
- Include a **Reset filters** action

### Event tap behavior
Tapping an event can open a details sheet or detail page showing:
- Full event title
- Full description
- Timestamp
- Tank
- Device
- Raw value if relevant
- Threshold if relevant
- Event source
- Correlation or event id
- Suggested next action if relevant

Example:
- Event: `High temperature warning`
- Current temp: `29.8°C`
- Threshold: `28.0°C`
- Source: `tank-controller-01`
- Suggested action: `Check heater, room temperature, and water flow`

---

## Empty States

### No events yet
Message:
- `No events yet`
- `Device activity and alerts will appear here`

### No results for filters
Message:
- `No events match your filters`
- Show action: `Clear filters`

---

## Loading and Error States

### Loading
- Use skeleton rows or shimmer placeholders
- Avoid blank screen

### Error
- Show a friendly retry state
- Example:
  - `Couldn’t load events`
  - `Please try again`

---

## Recommended Features for the Events Tab

These are important additions that would make this tab much better than a simple log screen.

## Must-have
1. **Filter chips**
   - Very useful for event-heavy systems
   - Makes the screen feel powerful without being complex

2. **Severity indicators**
   - Essential to separate info from actual problems

3. **Event details view**
   - Important for debugging device behavior

4. **Grouped timeline**
   - Easier to scan than one flat long list

5. **Pull to refresh**
   - Useful when testing live hardware behavior

---

## Strongly recommended
6. **Unread / new event marker**
   - Helps users notice fresh events since last visit

7. **Acknowledge for warnings**
   - Especially useful for repeated temp alerts
   - Prevents alert fatigue

8. **Event deduplication**
   - Example: if a device goes offline 5 times in 20 seconds, avoid spamming the list
   - Collapse repeated identical events into one grouped event

9. **Event source metadata**
   - Whether generated by app, backend, automation, or device
   - Good for debugging

10. **Human-friendly descriptions**
   - Avoid overly technical event text by default
   - Technical details can live inside event detail view

---

## Nice-to-have
11. **Search**
   - Search by tank name, event text, device name

12. **Export history**
   - Export events later as CSV or text log

13. **Pinned important events**
   - Keep unresolved critical issues visible

14. **Related event linking**
   - Example:
     - Device offline
     - Reconnected
     - Sensor values resumed
   - These can be shown as part of one incident chain

15. **Incident grouping**
   - Group multiple related warnings into one incident session

16. **Realtime auto-update**
   - New events appear live without full reload

17. **Silent vs actionable events**
   - Not every event needs the same visual emphasis

---

## What I Think Is Especially Important

For TankCtl specifically, these matter the most:

### 1) Distinguish informational vs actionable events
Users should instantly know:
- “This is just a log”
- or
- “This needs attention”

### 2) Make tank filtering very easy
If the user has multiple tanks, tank-based filtering becomes one of the most important UX features.

### 3) Keep event descriptions human-readable
Good:
- `Light turned ON from app`
- `Temperature exceeded safe threshold`

Less good:
- `relay_state_change event emitted by node-02`

### 4) Show recovery events
Not just bad events:
- `Temperature back to normal`
- `Device reconnected`

This builds confidence and helps users understand resolution, not just failures.

### 5) Avoid noisy spam
Aquarium or IoT systems can produce too many logs.
A clean events experience should:
- collapse duplicate noise
- prioritize important items
- stay readable

---

## Suggested Event Object Model

A basic model Copilot can work with:

```ts
type EventSeverity = 'info' | 'warning' | 'critical';

type EventCategory =
  | 'light'
  | 'temperature'
  | 'connectivity'
  | 'system';

interface TankEvent {
  id: string;
  tankId: string;
  tankName: string;
  deviceId?: string;
  deviceName?: string;
  category: EventCategory;
  type: string;
  title: string;
  description: string;
  severity: EventSeverity;
  timestamp: string;
  value?: string | number;
  threshold?: string | number;
  source?: 'device' | 'app' | 'backend' | 'automation';
  isAcknowledged?: boolean;
  isRead?: boolean;
}
```

---

## Suggested Frontend Components

Possible components for implementation:

- `MainTabScaffold`
- `DashboardTab`
- `EventsTab`
- `SettingsTab`
- `EventFilterBar`
- `EventFilterChip`
- `EventList`
- `EventListSection`
- `EventCard` or `EventRow`
- `EventDetailsSheet`
- `EmptyStateView`
- `ErrorStateView`

---

## Suggested Events Tab Sections

A good structure for the Events tab:

### Header
- Title
- Optional event count

### Quick filter chips
- All
- Critical
- Warnings
- Light
- Temperature
- Offline

### Advanced filters
- Tank dropdown
- Event type dropdown
- Time range dropdown
- Severity dropdown

### Event timeline list
- Grouped by date/time
- Newest first

---

## Suggested Interaction Flow

### Flow 1: User checks recent issue
1. Open Events tab
2. See critical event near top
3. Filter by tank
4. Tap event
5. Read detailed cause and timestamp
6. Go back or jump to dashboard/tank

### Flow 2: User audits light automation
1. Open Events tab
2. Filter by event type = Light
3. Filter by tank
4. Review ON/OFF history
5. Verify automation timing

### Flow 3: User investigates connectivity issue
1. Open Events tab
2. Filter by event type = Connectivity
3. Sort newest first
4. Inspect offline -> online sequence
5. Confirm recovery

---

## Dashboard and Events Relationship

These two tabs should complement each other:

### Dashboard
- Current state
- Quick summary
- Immediate actions

### Events
- Historical state
- Detailed timeline
- Troubleshooting and audit trail

A good pattern:
- Dashboard shows a small preview like “Recent events”
- Tapping that preview opens Events tab with relevant filters pre-applied

Example:
- Tap warning on tank card
- Navigate to Events tab filtered to that tank and warning category

---

## Settings Suggestions Related to Events

The Settings tab should include event-related settings such as:

### Notifications
- Enable push notifications
- Notify only for warning/critical
- Quiet hours
- Per-event-type notification control

### Thresholds
- High temperature threshold
- Low temperature threshold
- Offline timeout threshold

### History
- Retain event history for X days
- Clear local cache
- Sync behavior

### Preferences
- Default event sort
- Default filter presets
- Time format
- Temperature unit

---

## Recommended MVP for First Version

For a strong first version, build these first:

### Dashboard
- Tank list/cards
- Current temperature
- Light status
- Connectivity status
- Quick action buttons
- Small recent events preview

### Events
- Event list
- Event type filter
- Tank filter
- Severity filter
- Date grouping
- Event details sheet
- Empty / loading / error states

### Settings
- Notification settings
- Temperature thresholds
- Offline timeout
- Theme / app preferences

---

## Future Enhancements

Later improvements:
- Search
- Event export
- Incident grouping
- Analytics on events
- Trend insights
- “Most unstable tank/device” insights
- Rule-based automation history
- Bookmark or pin important incidents

---

## Copilot Build Notes

When generating the UI:
- keep it polished and modern
- avoid overly playful styling
- prioritize readability and filtering
- optimize for fast scanning
- make warnings and critical events visually distinct
- keep the Dashboard simple and glanceable
- keep the Events tab structured like a usable monitoring timeline
- keep Settings clean and grouped by category

Use a design that feels:
- practical
- calm
- modern
- slightly technical, but not cluttered

---

## Final Recommendation

If only a few things are done really well, make sure these are excellent:

1. Dashboard glanceability
2. Events filtering
3. Clear severity hierarchy
4. Good event descriptions
5. Smooth navigation between Dashboard and Events
6. Notification and threshold controls in Settings

That combination will make the app feel much more complete and useful.