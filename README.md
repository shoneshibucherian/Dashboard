# INT_Dashboard

## Configuration

Before starting the visualization, configure the `user_config.ini` file in the `microburst` folder.

## Running the Visualization

To **start** the visualization, run:

```bash
./start_viz
````

To **stop** the visualization, run:

```bash
./stop_viz
```

---

## Types of Visualizations

### 1. Count per Part of the Day vs Date

This graph is created by grouping the data **by days**, and each day is divided into four time segments.
This helps identify during which part of the day microbursts occur most frequently.

---

### 2. Key vs Time

This graph shows microbursts that occurred at each **key combination** during each day.

> The data can be grouped by:
>
> * Hour
> * Day
> * Month
> * Year

#### To change the grouping unit:

1. Go to the **Edit** section of the graph.
2. Go to **Query Inspection**.
3. Change the **Min Interval**.

##### Supported Min Intervals:

```text
1h  →  Group by hour
1d  →  Group by day
1M  →  Group by month
1y  →  Group by year
```

---

### 3. VLAN vs Time

This graph shows microbursts that occurred at each **VLAN ID** during each day.
Supports the same grouping flexibility as Key vs Time.

> **Note:**
>
> * **Key vs Time**: focuses on records where `vlan_id == 0`.
> * **VLAN vs Time**: focuses on records where `vlan_id != 0`.
>
> This distinction allows comparison between microbursts that occur at keys **not associated** with a VLAN and those that **are associated** with a VLAN.

---

### 4. Overall Microbursts at Each VLAN

Let `x` be a VLAN ID.

```text
bandFreq(x) = (Number of microbursts for VLAN x) × (Max Bandwidth)
```

```text
Percentage of microbursts for VLAN x = 
    (bandFreq(x) / Sum of bandFreq for all VLANs) × 100
```

---

### 5. Overall Microbursts at Each Key Combination

Let `x` be a key combination: `(switch:x, port:x, queue:x)`

```text
bandFreq(x) = (Number of microbursts for key x) × (Max Bandwidth)
```

```text
Percentage of microbursts for key x = 
    (bandFreq(x) / Sum of bandFreq for all keys) × 100
```

