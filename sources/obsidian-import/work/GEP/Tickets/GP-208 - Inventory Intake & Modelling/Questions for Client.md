# GP-208 — Inventory Feed: Questions for GEP/Navira


Hi team — before we start building, we have a few questions to make sure we set this up correctly the first time. Most of these have a "yes/no" or short answer.


---


## 1. Where is the data coming from?

  
Previously, inventory data was pulled directly from Sellercloud and Amazon — both of which already feed into our system.


**Is the new inventory feed coming from those same systems, or is it coming from somewhere new?**


- If it's the same — we may already have what we need and can get started quickly.

- If it's new — we'll need a few technical details to connect to it (see Section 2).

  

---

  

## 2. How will the data be delivered? *(only if the source is new)*

  
Our preferred option is a **Snowflake data share** — a direct, secure connection between your Snowflake account and ours. If that's the route, we'll need:


- Your Snowflake account name

- The name of the table or view being shared

- How often the data refreshes (e.g., hourly, daily?)

- What timezone the "Capture Date" timestamp uses (e.g., Eastern, UTC?)

- How far back you'd like us to load historical data
  

~~**If a data share isn't ready yet**, we can temporarily accept a CSV file drop as a stopgap — in which case: who sends it, how often, and is there a way to include a row count so we can confirm nothing was lost in transit?~~

  

---

  

## 3. What does "Iteration" mean?


Every row in the sample data has a field called **Iteration** (currently showing as 46).


**What does this number represent?**


For example:

- Is it a batch counter that goes up by 1 each time data is refreshed?

- Does it represent a planning cycle or version number?

- Can there be more than one Iteration per day?

  

---

  

## 4. A few column definitions we need confirmed

  
We want to make sure we label and use these correctly.


**a) AWD columns** — the sample includes "AWD InT" and "AWD Available."

What does AWD stand for in your context, and what facility or program does it refer to?


**b) Kit columns** — "Pending Kit Qty," "Working Kit Qty," and "FBM Offered Kit Qty" are all showing as zero in the sample.

What do these represent, and should we expect them to have real values in production?


**c) FBA breakdowns** — the data has both a "Total US FBA Available" and a "US FBA Available."

Is "Total" simply the sum of the detail columns, or is there a difference?

Same question for "Total Non Sellable" vs. "Non Sellable Qty."


**d) Canada FBA** — there's a "CA FBA Available" column, currently zero in the sample.

Is this Canada-specific FBA inventory? Will it populate over time?


**e) Reserved columns** — some values in the reserved FBA columns (e.g., "US FBA Rsrvd Orders") show as negative numbers.

Is this expected — for example, a correction or adjustment — or is it a data issue we should flag?

  

---


## 5. How should we handle historical data?

  
**Do you want us to keep a full history of snapshots** (so you can see what inventory looked like on any given date), or should we only ever show the most recent snapshot?


We recommend keeping full history — it makes trend analysis and "days of supply" reporting possible. But we want to confirm this is what you're after.

  

---

  
## 6. What would you like us to build first?


To help us prioritize, **what are the first one or two reports or decisions this data needs to support?**


For example:

- Checking how many days of stock you have left for each product

- Identifying which products are running low across all warehouses

- Tracking AWD replenishment

  
Knowing this helps us focus on the right columns and make sure the data is ready for your most important use case first.

  

---


## 7. On-order quantities


The sample includes an "On Order GEP2 Qty" column — the number of units currently on order.


We already have on-order data flowing through our system from Sellercloud purchase orders.


**Should we use the value from your feed directly, or pull it from the purchase order data we already have?** Either works — we just want to make sure they match and we're not double-counting.

  

---

  

*Thanks in advance — answers to these will let us get started right away.*