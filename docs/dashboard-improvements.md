# Dashboard Improvement Ideas

The dashboard is already clean, but it is still mostly a list plus a summary card. The next improvements should focus on triage, trend visibility, and operator speed.

## High-Value Improvements

### 1. Critical Issues Strip
Add a compact "Needs Attention" section above the tank list.

Show only actionable problems:
- Offline tanks
- High temperature
- Low temperature
- No Temp Sensor

This would make the dashboard useful at a glance instead of forcing users to scan each card.

### 2. Sort Modes
Right now there is only an `Online only` filter.

Add sort options such as:
- Most recently updated
- Hottest tank
- Warning first
- Offline first

This would make the dashboard operational instead of purely alphabetical.

### 3. Better Overview Card
Upgrade the overview card from:
- online count
- average temperature

To also include:
- warning count
- offline count
- average temperature for online tanks only
- hottest tank
- coldest tank

This would make the overview card informational instead of mostly decorative.

### 4. Per-Tank Reason Subtitle
Each tank card should explain *why* it is in its current state.

Examples:
- `No telemetry for 12m`
- `Sensor unavailable`
- `Temp above threshold`
- `Light on`

This reduces the need to open the detail screen just to understand status.

### 5. More Informative Mini Chart
Improve the sparkline by adding:
- normal temperature band
- last-point highlight
- high/low threshold markers

This would help detect drift instead of just showing raw shape.

### 6. Quick Actions
Expose common actions directly on the card or dashboard.

Examples:
- Toggle light
- Acknowledge warning
- Open detail
- Refresh this tank only

This improves operator speed for frequent tasks.

### 7. Connection Quality Indicators
If heartbeat includes `rssi`, Wi-Fi status, or firmware version, show a compact quality/status area.

Examples:
- Strong or weak Wi-Fi
- Firmware version
- Stale vs live connection

This makes "online" more meaningful than a simple binary dot.

### 8. Event Timeline Panel
Add a recent events section for quick system visibility.

Examples:
- `tank1 online`
- `tank2 no temp sensor`
- `tank1 light on`
- `tank3 temp recovered`

This gives confidence that the system is alive without checking logs.

### 9. Saved Dashboard Views
Add preset views such as:
- All
- Online
- Warnings
- Offline
- Sensor Issues

This scales better than a single filter chip.

### 10. Better Empty/Error State
When backend connectivity fails, show more useful diagnostics:
- Retry button
- Current configured backend URL
- WebSocket status
- Last successful sync time

This makes mobile debugging much easier.

## Recommended Next 3

If prioritizing for impact and speed:

1. Critical Issues Strip
2. Sort Modes
3. Event Timeline Panel