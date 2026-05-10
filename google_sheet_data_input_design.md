#  Grand Design: Google Sheets Data Input

  ---
  1. The Data Universe — What a Shrimp Farmer Actually Tracks

  Tab 1: DAILY_LOG — One row per day per cycle

  ┌─────┬────────────────────┬────────────┬──────────┬─────────────────────────────────────────────────────────────┐
  │ Col │       Field        │    Type    │ Required │                            Notes                            │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ A   │ Date               │ date       │ ✅       │ Normalized to YYYY-MM-DD                                    │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ B   │ DOC                │ int        │ —        │ Auto-computed from start_date if blank                      │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ C   │ DO Morning         │ float mg/L │ —        │ Range 0–20                                                  │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ D   │ DO Afternoon       │ float mg/L │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ E   │ DO Average         │ float mg/L │ —        │ Auto-computed if C+D present                                │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ F   │ Temp Morning       │ float °C   │ —        │ Range 15–40                                                 │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ G   │ Temp Afternoon     │ float °C   │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ H   │ Temp Average       │ float °C   │ —        │ Auto-computed                                               │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ I   │ pH Morning         │ float      │ —        │ Range 6–9                                                   │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ J   │ pH Afternoon       │ float      │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ K   │ Salinity           │ float ppt  │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ L   │ NH3                │ float mg/L │ —        │ Threshold: > 0.3 → alert                                    │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ M   │ Turbidity (Secchi) │ float cm   │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ N   │ Feed Given (kg)    │ float      │ —        │ Daily total                                                 │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ O   │ Feed Leftover (kg) │ float      │ —        │ MISSING from current template — critical for feeding engine │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ P   │ Feed Type          │ string     │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤
  │ Q   │ Protein %          │ float      │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤                                                         
  │ R   │ Feeding Freq       │ int        │ —        │                                                             │
  ├─────┼────────────────────┼────────────┼──────────┼─────────────────────────────────────────────────────────────┤                                                         
  │ S   │ Notes              │ string     │ —        │                                                             │                                                       
  └─────┴────────────────────┴────────────┴──────────┴─────────────────────────────────────────────────────────────┘

  Tab 2: ABW_SAMPLING — One row per sampling event (~every 7–10 days)                                                                                                        
   
  ┌─────┬─────────────────────────┬────────┬──────────┐                                                                                                                      
  │ Col │          Field          │  Type  │ Required │                                                                                                                    
  ├─────┼─────────────────────────┼────────┼──────────┤
  │ A   │ Date                    │ date   │ ✅       │
  ├─────┼─────────────────────────┼────────┼──────────┤
  │ B   │ DOC                     │ int    │ — auto   │                                                                                                                      
  ├─────┼─────────────────────────┼────────┼──────────┤
  │ C   │ Sample Count            │ int    │ —        │                                                                                                                      
  ├─────┼─────────────────────────┼────────┼──────────┤                                                                                                                    
  │ D   │ Total Sample Weight (g) │ float  │ —        │
  ├─────┼─────────────────────────┼────────┼──────────┤                                                                                                                      
  │ E   │ ABW (g)                 │ float  │ ✅       │
  ├─────┼─────────────────────────┼────────┼──────────┤                                                                                                                      
  │ F   │ Min Weight (g)          │ float  │ —        │                                                                                                                    
  ├─────┼─────────────────────────┼────────┼──────────┤
  │ G   │ Max Weight (g)          │ float  │ —        │
  ├─────┼─────────────────────────┼────────┼──────────┤                                                                                                                      
  │ H   │ CV%                     │ float  │ —        │
  ├─────┼─────────────────────────┼────────┼──────────┤                                                                                                                      
  │ I   │ Sampled By              │ string │ —        │                                                                                                                    
  ├─────┼─────────────────────────┼────────┼──────────┤
  │ J   │ Notes                   │ string │ —        │
  └─────┴─────────────────────────┴────────┴──────────┘

  Tab 3: COST — Multiple rows per day allowed                                                                                                                                
   
  ┌─────┬──────────────────┬────────┬──────────┐                                                                                                                             
  │ Col │      Field       │  Type  │ Required │                                                                                                                           
  ├─────┼──────────────────┼────────┼──────────┤
  │ A   │ Date             │ date   │ ✅       │
  ├─────┼──────────────────┼────────┼──────────┤
  │ B   │ Category         │ string │ ✅       │
  ├─────┼──────────────────┼────────┼──────────┤                                                                                                                             
  │ C   │ Description      │ string │ —        │
  ├─────┼──────────────────┼────────┼──────────┤                                                                                                                             
  │ D   │ Quantity         │ float  │ —        │                                                                                                                           
  ├─────┼──────────────────┼────────┼──────────┤
  │ E   │ Unit             │ string │ —        │
  ├─────┼──────────────────┼────────┼──────────┤                                                                                                                             
  │ F   │ Unit Price (IDR) │ float  │ —        │
  ├─────┼──────────────────┼────────┼──────────┤                                                                                                                             
  │ G   │ Total (IDR)      │ float  │ ✅       │                                                                                                                           
  ├─────┼──────────────────┼────────┼──────────┤
  │ H   │ Vendor           │ string │ —        │
  ├─────┼──────────────────┼────────┼──────────┤                                                                                                                             
  │ I   │ Notes            │ string │ —        │
  └─────┴──────────────────┴────────┴──────────┘                                                                                                                             
                                                                                                                                                                           
  Tab 4: HARVEST — One row per harvest event

  ┌─────┬────────────────────┬────────┬─────────────┐
  │ Col │       Field        │  Type  │  Required   │
  ├─────┼────────────────────┼────────┼─────────────┤
  │ A   │ Date               │ date   │ ✅          │
  ├─────┼────────────────────┼────────┼─────────────┤
  │ B   │ DOC                │ int    │ — auto      │
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ C   │ Is Partial? (Y/N)  │ string │ — default N │
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ D   │ Biomass (kg)       │ float  │ ✅          │                                                                                                                      
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ E   │ ABW at Harvest (g) │ float  │ —           │
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ F   │ SR at Harvest (%)  │ float  │ —           │                                                                                                                      
  ├─────┼────────────────────┼────────┼─────────────┤
  │ G   │ Bags/Count         │ int    │ —           │
  ├─────┼────────────────────┼────────┼─────────────┤
  │ H   │ Buyer              │ string │ —           │
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ I   │ Price/kg (IDR)     │ float  │ —           │
  ├─────┼────────────────────┼────────┼─────────────┤                                                                                                                        
  │ J   │ Notes              │ string │ —           │                                                                                                                      
  └─────┴────────────────────┴────────┴─────────────┘

  Tab 5: MORTALITY — One row per day (daily dead count)

  ┌─────┬────────────┬────────┬──────────┐                                                                                                                                   
  │ Col │   Field    │  Type  │ Required │
  ├─────┼────────────┼────────┼──────────┤                                                                                                                                   
  │ A   │ Date       │ date   │ ✅       │                                                                                                                                 
  ├─────┼────────────┼────────┼──────────┤
  │ B   │ DOC        │ int    │ — auto   │
  ├─────┼────────────┼────────┼──────────┤
  │ C   │ Dead Count │ int    │ ✅       │
  ├─────┼────────────┼────────┼──────────┤
  │ D   │ Notes      │ string │ —        │
  └─────┴────────────┴────────┴──────────┘                                                                                                                                   
   
  ---                                                                                                                                                                        
  2. Deduplication Strategy — Per-Tab                                                                                                                                      
                                     
  This is the most important design decision. Current code uses insert-if-not-exists by date string — this is wrong for two reasons: (1) date format variance creates false
  duplicates, (2) farmer corrections on the sheet never get applied.                                                                                                         
   
  ┌──────────────┬─────────────────────────────────────────┬────────────────────────────────┬────────────────────────────────────────────────────┐                           
  │     Tab      │                   Key                   │            Strategy            │                     Rationale                      │                         
  ├──────────────┼─────────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────────────────────┤
  │ DAILY_LOG    │ (cycle_id, date)                        │ UPSERT — merge non-null fields │ Farmer corrects a DO reading → re-sync reflects it │
  ├──────────────┼─────────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────────────────────┤
  │ ABW_SAMPLING │ (cycle_id, date)                        │ UPSERT                         │ One sampling event per day                         │                           
  ├──────────────┼─────────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────────────────────┤                           
  │ COST         │ (cycle_id, date, category, description) │ INSERT if not exists           │ Multiple different purchases on same day are valid │                           
  ├──────────────┼─────────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────────────────────┤                           
  │ HARVEST      │ (cycle_id, date)                        │ UPSERT                         │ One harvest event per date                         │                         
  ├──────────────┼─────────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────────────────────┤                           
  │ MORTALITY    │ (cycle_id, date)                        │ UPSERT                         │ One mortality count per day                        │                         
  └──────────────┴─────────────────────────────────────────┴────────────────────────────────┴────────────────────────────────────────────────────┘                           
   
  UPSERT rule: when date match found, merge new values into existing record — only non-null new values overwrite existing. A field deleted in the sheet (now blank) does NOT 
  erase the existing DB value.                                                                                                                                             
                                                                                                                                                                             
  ---                                                                                                                                                                      
  3. Date Handling — The Root of All Bugs
                                                                                                                                                                             
  Google Sheets returns dates as strings in the spreadsheet's locale format. Indonesian locale returns "15/01/2024". A user typing manually might enter "2024-01-15" or "Jan 
  15" or "15-Jan-24".                                                                                                                                                        
                                                                                                                                                                           
  All dates must be normalized to YYYY-MM-DD before any dedup or insert. The dedup key uses the normalized form.                                                             
                                                                                                                                                                           
  Supported input formats → normalized output:                                                                                                                               
  - YYYY-MM-DD → YYYY-MM-DD (already correct)                                                                                                                              
  - DD/MM/YYYY → normalize (Indonesian default)                                                                                                                              
  - MM/DD/YYYY → normalize (ambiguous — use locale hint)
  - DD-MM-YYYY → normalize                                                                                                                                                   
  - DD-Mon-YY (e.g. 15-Jan-24) → normalize                                                                                                                                   
  - DD Month YYYY → normalize                                                                                                                                                
                                                                                                                                                                             
  DOC auto-computation: if column B is blank, compute (normalized_date - cycle.start_date).days. This removes a whole class of user errors.                                  
                                                                                                                                                                             
  Average auto-computation: if DO Average (E) is blank but DO Morning (C) and DO Afternoon (D) are present → do_avg = (do_morning + do_afternoon) / 2. Same for Temp and pH. 
                                                                                                                                                                             
  ---                                                                                                                                                                        
  4. Cascade — Where Data Flows After Sync                                                                                                                                 
                                                                                                                                                                             
  DAILY_LOG rows ──────────────────► CycleData.result_data[] (UPSERT by date)
                       └──────────► FeedRealization (UPSERT by doc) ← feeds the ML engine                                                                                    
                       └──────────► Anomaly alerts (check thresholds per row)                                                                                                
                                                                                                                                                                             
  ABW_SAMPLING rows ───────────────► CycleData.result_data[] (MERGE into date entry)                                                                                         
                                                                                                                                                                             
  COST rows ───────────────────────► CostData.data[] (INSERT if not exists)                                                                                                  
                                                                                                                                                                           
  HARVEST rows ────────────────────► HarvestRecord (UPSERT by date)                                                                                                          
                                                                                                                                                                           
  MORTALITY rows ──────────────────► CycleData.result_data[] (merge mortality_count by date)                                                                                 
   
  After total_inserted > 0:                                                                                                                                                  
    └──────────────────────────────► Mark ForecastData as stale (needs recompute)                                                                                          
    └──────────────────────────────► Run alert generation for anomalies in new rows                                                                                          
                                                                                                                                                                             
  Why FeedRealization must be populated: The feeding recommendation engine's leftover-feedback loop reads FeedRealization.feed_leftover. If this model is empty, the engine  
  always uses base ration with no leftover adjustment — defeating the adaptive feeding feature entirely for sheet users.                                                     
                                                                                                                                                                             
  ---                                                                                                                                                                      
  5. The Sync Algorithm
                                                                                                                                                                             
  sync_cycle(cycle_id):
                                                                                                                                                                             
    SETUP:                                                                                                                                                                 
      load SheetIntegration → validate is_active → get spreadsheet_id
      load Cycle → get start_date (for DOC auto-fill)                                                                                                                        
      build Sheets API service
      set integration.last_status = "syncing" → save (acts as optimistic lock)                                                                                               
                                                                                                                                                                           
    For each tab [DAILY_LOG, ABW_SAMPLING, COST, HARVEST, MORTALITY]:                                                                                                        
                                                                                                                                                                           
      read_rows(spreadsheet_id, tab, start_row=3)                                                                                                                            
                                                                                                                                                                           
      for row in rows:                                                                                                                                                       
        if row is empty → skip                                                                                                                                             
        raw_date = row[0]                                                                                                                                                    
        normalized_date = _normalize_date(raw_date) → if None: reject
        doc = row[1] if present else (normalized_date - start_date).days                                                                                                     
        parse remaining fields with _safe_float/_safe_int/_safe_str                                                                                                          
        auto-compute averages where applicable                                                                                                                               
        run validation (range checks) → flag anomalies but don't reject                                                                                                      
        check dedup key against existing records                                                                                                                             
        if INSERT strategy and key exists → skipped                                                                                                                          
        if UPSERT strategy and key exists → merge non-null new fields                                                                                                        
        if key not found → new insert                                                                                                                                        
                                                                                                                                                                             
      persist to MongoDB                                                                                                                                                   
      write SYNC_LOG entry                                                                                                                                                   
                                                                                                                                                                           
    POST-SYNC CASCADES:                                                                                                                                                      
      for each newly inserted/updated DAILY_LOG row:
        if feed_given_kg is not None and doc is not None:                                                                                                                    
          upsert FeedRealization(cycle_id=cycle_id, doc=doc,                                                                                                                 
                                 feed_given=feed_given_kg,                                                                                                                   
                                 feed_leftover=feed_leftover_kg)                                                                                                             
                                                                                                                                                                             
      if total_inserted + total_updated > 0:                                                                                                                                 
        generate water quality alerts for rows with anomalies
        mark cycle forecast as stale                                                                                                                                         
                                                                                                                                                                             
    FINALIZE:
      integration.last_synced = now                                                                                                                                          
      integration.last_status = "ok" if no errors else "error" or "partial"                                                                                                
      integration.rows_synced += total_inserted                                                                                                                              
      integration.save()                                                                                                                                                     
                                                                                                                                                                             
    return summary                                                                                                                                                           
                                                                                                                                                                           
  ---                                                                                                                                                                        
  6. Template Creation — The Full Flow                                                                                                                                     
                                      
  Current: service account creates file → it's in service account's Drive → user can't find it → has to manually connect.
                                                                                                                                                                             
  Correct flow:
  create_template(cycle_id, user_id, user_email):                                                                                                                            
    1. Build Sheets service + Drive service (same credentials)                                                                                                             
    2. Load Cycle + Pond for metadata                         
    3. Create spreadsheet (owned by service account)                                                                                                                         
    4. Write SETUP tab with cycle metadata                                                                                                                                   
    5. Write headers (rows 1–2) for all 5 data tabs + SYNC_LOG                                                                                                               
       Row 1: Column names                                                                                                                                                   
       Row 2: Units/description hints (e.g. "mg/L", "°C", "kg")                                                                                                              
    6. Share with user_email as Editor via Drive API                                                                                                                       
    7. Auto-create SheetIntegration record (cycle already connected)                                                                                                         
    8. Return { spreadsheet_id, spreadsheet_url, auto_connected: true }                                                                                                      
                                                                                                                                                                             
  After creation, frontend auto-refreshes to the "connected" state — no manual ID entry needed.                                                                              
                                                                                                                                                                             
  ---                                                                                                                                                                        
  7. User Journey                                                                                                                                                            
                                                                                                                                                                             
  Journey A: New cycle, creating a fresh sheet
  Cycle detail → Google Sheets tab                                                                                                                                           
    → "No sheet connected" state                                                                                                                                           
    → Click "Create Template"                                                                                                                                                
    → Sheet created, shared to user's email, auto-connected                                                                                                                  
    → UI transitions to "Connected" state                                                                                                                                    
    → User opens sheet link → sees SETUP pre-filled, headers in all tabs                                                                                                     
    → User fills daily data in DAILY_LOG                                                                                                                                   
    → Returns to Teramina → clicks "Sync Now"                                                                                                                                
    → Celery task runs → data imported                                                                                                                                       
    → UI polls until last_status changes from "syncing"                                                                                                                      
    → Shows "Synced 7 rows from DAILY_LOG, 1 from ABW_SAMPLING"                                                                                                              
    → Forecasts and feeding recommendations now have data                                                                                                                    
                                                                                                                                                                             
  Journey B: Connecting an existing sheet                                                                                                                                    
  Google Sheets tab                                                                                                                                                          
    → Enters spreadsheet URL or ID                                                                                                                                           
    → Click "Connect"                                                                                                                                                      
    → Backend validates access (reads SETUP tab)
    → Integration record created                                                                                                                                             
    → UI shows "Connected — sync to import your data"
    → Click "Sync Now" → all historical data imported                                                                                                                        
    → Summary shows total rows by tab                                                                                                                                        
   
  Journey C: Daily ongoing use (automated)                                                                                                                                   
  Farmer fills yesterday's row in Google Sheets (on phone, anywhere)                                                                                                       
    → Celery Beat (every 30 min) runs sync_all_active_sheets()                                                                                                               
    → New row detected → imported into CycleData                                                                                                                             
    → FeedRealization updated                                                                                                                                                
    → Feeding recommendation for today's DOC uses updated leftover ratio                                                                                                     
    → If DO < 3 mg/L → alert generated → appears in AI Assistant badge                                                                                                       
    → Next time farmer opens Teramina → dashboard already updated                                                                                                            
                                                                                                                                                                             
  Journey D: Correcting bad data                                                                                                                                             
  Farmer notices NH3 was entered wrong 3 days ago                                                                                                                            
    → Fixes the value in the Google Sheet                                                                                                                                    
    → Clicks "Sync Now" in Teramina                                                                                                                                          
    → UPSERT finds the existing date entry                                                                                                                                   
    → NH3 field updated in CycleData.result_data                                                                                                                             
    → Alert that was triggered by the bad value is now rechecked                                                                                                             
                                                                                                                                                                             
  ---                                                                                                                                                                        
  8. What the Frontend Status States Must Show                                                                                                                               
                                                                                                                                                                             
  ┌─────────────────────┬─────────────────────────────────────┬─────────────────────────────────────────────────┐                                                          
  │        State        │               Trigger               │                       UI                        │                                                            
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤                                                          
  │ No integration      │ get_status returns is_active: false │ "Connect" form + "Create Template" button       │
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Connected / pending │ is_active: true, never synced       │ "Connected — sync to import data"               │                                                            
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤                                                            
  │ Syncing             │ last_status = "syncing"             │ Spinning indicator, "Syncing…", disable buttons │                                                            
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤                                                            
  │ Synced OK           │ last_status = "ok"                  │ Last sync time, rows count, green chip          │                                                          
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤                                                            
  │ Synced partial      │ last_status = "partial"             │ Yellow chip, show which tabs had errors         │                                                          
  ├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────────────────┤                                                            
  │ Error               │ last_status = "error"               │ Red chip, show last_error message               │                                                          
  └─────────────────────┴─────────────────────────────────────┴─────────────────────────────────────────────────┘                                                            
                                                                                                                                                                           
  get_status must return 200 with is_active: false (not 400) when no integration exists. The frontend should never need to interpret 4xx to render the "not connected" state.
                                                                                                                                                                           
  ---                                                                                                                                                                        
  9. Gaps in Current Implementation Summary                                                                                                                                
                                           
  ┌─────┬────────────────────────────────────────────┬───────────────────────────────────────────┬──────────────────────────────────┐
  │  #  │                   Issue                    │                  Impact                   │               Fix                │                                        
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤
  │ 1   │ get_status returns 400 when no integration │ "Sheets" tab shows blank                  │ Return 200 with is_active: false │                                        
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                      
  │ 2   │ status.connected field doesn't exist       │ "Not connected" UI never renders          │ Check status.is_active           │                                        
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 3   │ handleSync sends cycle_id in body          │ Sync 422 errors                           │ Query param                      │                                        
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 4   │ Toast "Sync complete" on async task        │ User confusion                            │ "Sync queued" + poll             │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 5   │ last_status === "success" chip check       │ Chip always red                           │ Backend uses "ok"                │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 6   │ No date normalization                      │ Duplicates on format variance             │ _normalize_date()                │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 7   │ No DOC auto-computation                    │ Users must compute DOC manually           │ Derive from start_date           │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 8   │ No average auto-computation                │ Extra work for user                       │ If morning+afternoon, fill avg   │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 9   │ INSERT instead of UPSERT for DAILY_LOG/ABW │ Corrections don't apply                   │ Change to UPSERT                 │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 10  │ feed_leftover missing from template        │ Feeding engine has no leftover ratio      │ Add column O                     │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 11  │ FeedRealization never populated            │ Feeding ML completely blind to sheet data │ Cascade from DAILY_LOG           │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 12  │ HARVEST tab: no headers, not synced        │ Feature silently useless                  │ Add headers + sync               │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 13  │ MORTALITY tab: no headers, not synced      │ Feature silently useless                  │ Add headers + sync               │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 14  │ Template in service account Drive only     │ User can't access created sheet           │ Drive sharing API                │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 15  │ No auto-connect after template creation    │ UX friction, manual copy-paste            │ Auto-connect after create        │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 16  │ last_status never set to "syncing"         │ No UI lock during async sync              │ Set before queuing task          │                                      
  ├─────┼────────────────────────────────────────────┼───────────────────────────────────────────┼──────────────────────────────────┤                                        
  │ 17  │ No anomaly alerts from sync                │ Sheet users miss water quality warnings   │ Post-sync alert generation       │                                      
  └─────┴────────────────────────────────────────────┴───────────────────────────────────────────┴──────────────────────────────────┘                                        
                                   