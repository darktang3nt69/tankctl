---
title: CHROME_PERFORMANCE_TESTING
type: note
permalink: tankctl/tankctl-app/chrome-performance-testing
---

# Chrome Performance Testing Guide

## Quick Start

The Flutter web app is now running in Chrome. Follow this guide to verify performance optimizations.

### 1. Access the App

Navigate to: **http://localhost:54829** (or the URL shown in the terminal)

### 2. Open Chrome DevTools

Press **F12** or **Right-Click → Inspect**

## Performance Testing Checklist

### ✓ Frame Rate Monitor

**Steps:**
1. Open DevTools (F12)
2. Go to **Performance** tab
3. Click the red **Record** circle
4. Interact with the app for 5-10 seconds:
   - Watch particles animate (background)
   - Tap cards or buttons
   - Open modal dialogs
5. Stop recording (red dot again)

**What to Look For:**
- Green bars = ✅ Good (<16ms per frame)
- Yellow bars = ⚠️ Concerning (16-33ms per frame)
- Red bars = ❌ Slow (>33ms per frame)

**Target Result:** 
- 60+ FPS consistently during interactions
- No dropped frames during particle animation
- Smooth transitions on modal reveals

### ✓ Paint Performance

**In Performance Recording:**
1. Look for "Paint" events in the timeline
2. High paint count = excessive repaints (bad)
3. Low paint count = efficient rendering (good)

**Expected** (after optimizations):
- Particle animation: 1-2 paints per frame (RepaintBoundary isolated)
- Card interaction: 0-1 paints per frame (ScaleTransition isolated)
- Total paint time: <5ms per frame

### ✓ Main Thread Usage

**In Performance Recording:**
1. Bottom section shows main thread work
2. Look for gaps between busy periods
3. Large gaps = dropped frames (bad)
4. Consistent activity = smooth rendering (good)

**Target:**
- Main thread should use <12ms per 16ms frame (60 FPS budget)

### ✓ Memory Usage

**Steps:**
1. DevTools → **Memory** tab
2. Click camera icon to take heap snapshot
3. Interact with app for 30 seconds
4. Take another snapshot
5. Check memory growth

**Expected (Chrome):**
- Baseline: ~80-120 MB
- After 30s interaction: <160 MB (stable)
- No continuous growth = ✅ No memory leak

### ✓ First Contentful Paint (FCP)

**In Performance Recording:**
1. Look for blue bar labeled "FCP"
2. Should appear within 2-3 seconds

**Target:**
- FCP < 2 seconds
- LCP (Largest Contentful Paint) < 2.5 seconds

## Interaction Performance Tests

### Test 1: Particle Background Animation

**Steps:**
1. Load app (particles start animating immediately)
2. Record Performance
3. Let it run for 5 seconds without interacting
4. Stop recording

**Verify:**
- ✅ Particles smoothly panning across screen
- ✅ Connection lines animating
- ✅ No jank or stuttering
- ✅ 60 FPS maintained throughout

### Test 2: Card Tap Feedback

**Steps:**
1. Record Performance
2. Rapidly tap 5-10 cards (quick taps)
3. Stop recording

**Verify:**
- ✅ Cards scale/fade smoothly on tap
- ✅ No frame drops during scale animation
- ✅ Quick response to tap (< 50ms delay)
- ✅ No ripple/jank in content

### Test 3: Modal Dialog Performance

**Steps:**
1. Record Performance
2. Open a modal dialog (if available)
3. Interact with modal content
4. Close dialog
5. Stop recording

**Verify:**
- ✅ Entrance animation smooth (scale/slide)
- ✅ Dialog content renders smoothly
- ✅ Close animation smooth
- ✅ No jank during backdrop blur effect

### Test 4: Filter Chips Performance

**Steps:**
1. Record Performance
2. Click multiple filter chips rapidly
3. Stop recording

**Verify:**
- ✅ Chips respond immediately to taps
- ✅ Selection state changes instantly
- ✅ No frame drops during state update
- ✅ Particle animation continues smoothly

## Advanced Performance Profiling

### CPU Throttling (Simulate Slower Device)

1. DevTools → **Performance** tab
2. Click ⚙️ settings (gear icon)
3. Check "Disable JavaScript samples" (optional)
4. Click 3-dot menu → "Capture Settings"
5. Set CPU throttling: **2x slow-down** or **4x slow-down**
6. Run tests again

**Why:** Ensures app performs well on slower hardware

### Network Throttling

1. DevTools → **Network** tab
2. Click throttle dropdown (usually "No throttling")
3. Select "Fast 3G" or "Slow 3G"
4. Reload app
5. Check load performance

**Note:** Web app should be mostly ready after network load

## Performance Metrics Dashboard

### Create a Metrics Snapshot

After all tests, document results:

```
CHROME WEB PERFORMANCE REPORT
=============================

Test Date: [Date]
Device: [Browser/OS]
Build: Release

FRAME RATE
- Idle (particles only): [FPS] ✅ / ⚠️ / ❌
- Card interactions: [FPS] ✅ / ⚠️ / ❌
- Modal dialogs: [FPS] ✅ / ⚠️ / ❌
- All interactions: [FPS] ✅ / ⚠️ / ❌

TIMING
- First Contentful Paint (FCP): [ms] ✅ / ⚠️ / ❌ (target: <2000ms)
- Largest Contentful Paint (LCP): [ms] ✅ / ⚠️ / ❌ (target: <2500ms)

MEMORY
- Baseline: [MB]
- After interaction: [MB]
- Growth: [MB] ✅ / ⚠️ / ❌ (should be <50MB)

PAINT OPERATIONS
- Per frame average: [count] ✅ / ⚠️ / ❌
- Max paint time: [ms]

JAVASCRIPT PARSING
- Initial load: [ms]
- On interactions: [ms]

OVERALL ASSESSMENT
[EXCELLENT] / [GOOD] / [ACCEPTABLE] / [NEEDS WORK]

Notes:
-------
```

## Optimization Verification

### Expected Improvements (Post-Optimization)

| Metric | Before | After | Status |
|--------|--------|-------|--------|
| Paint ops (particles) | 8-10/frame | 1-2/frame | ✅ Optimized |
| Paint ops (cards) | 3-5/frame | 0-1/frame | ✅ Optimized |
| Paint time | 8-12ms | 3-5ms | ✅ Reduced |
| Memory growth | 100MB+ | <50MB | ✅ Stable |
| FPS consistency | 45-55 FPS | 58-60 FPS | ✅ Improved |

## Troubleshooting

### Issue: Particles Stuttering

**Possible Causes:**
1. JavaScript parsing delays
2. Heavy content rendering
3. CPU throttling enabled

**Solutions:**
- Check CPU usage in Performance tab
- Reduce particle count (if configurable)
- Disable extensions that consume resources
- Use incognito mode (fewer extensions)

### Issue: Slow Initial Load

**Possible Causes:**
1. Large JS bundle
2. Network throttling
3. System under load

**Solutions:**
- Check Network tab for slow resources
- Verify network throttling disabled
- Close other browser tabs
- Reload app (should be cached after first load)

### Issue: High Memory Usage

**Possible Causes:**
1. Unfreed listeners
2. Animation accumulation
3. DOM bloat

**Solutions:**
- Close unused tabs
- Reload app to reset memory
- Check for memory leaks in DevTools
- Monitor for objects not being garbage collected

## Summary

✅ **Performance Optimization Goals:**
- [ ] 60 FPS maintained during all interactions
- [ ] Frame rate consistent (no drops)
- [ ] Memory stable (<200 MB on Chrome)
- [ ] Paint operations minimal (<5ms per frame)
- [ ] First Contentful Paint <2 seconds
- [ ] Responsive UI (tap feedback < 50ms)

**Next Steps:**
1. Run through all tests above
2. Document metrics (use template above)
3. Compare with targets
4. If issues found, refer to troubleshooting
5. File performance issues if metrics don't meet targets

---

**Questions or Issues?** Check the Performance Guide: [docs/PERFORMANCE.md](../docs/PERFORMANCE.md)