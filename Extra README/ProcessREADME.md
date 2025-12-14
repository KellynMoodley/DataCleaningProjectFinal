# Fecthing data from Google sheets, batch data validation and processing and storing in the database - Execution Logs

![alt text](images1.png)
![alt text](images2.png)

## Processing Data Execution Log

``` 
2025-12-14 21:42:31,322 [INFO] Fetching data from Google Sheets: April 2025...
2025-12-14 21:42:47,915 [INFO] ✓ Fetched 1,047,527 rows from Google Sheets in 16.6s
2025-12-14 21:42:47,915 [INFO] Creating original table: clients_2025_apr_2025_original
2025-12-14 21:42:48,210 [INFO] ✅ Executed SQL successfully
2025-12-14 21:42:48,504 [INFO] ✅ Executed SQL successfully
2025-12-14 21:42:48,504 [INFO] ✅ Cleared table: clients_2025_apr_2025_original
2025-12-14 21:42:48,504 [INFO] Processing 1,047,527 rows in 11 batches of 100,000...
2025-12-14 21:42:48,504 [INFO]
Processing batch 1/11 (rows 1 to 100000)...
2025-12-14 21:42:48,921 [INFO] Starting to clean 100000 rows...
2025-12-14 21:42:49,232 [INFO] Processed 100000 rows...
2025-12-14 21:42:49,240 [INFO] Cleaning complete: 69848 included, 30152 excluded
2025-12-14 21:42:49,246 [INFO] Batch 1: Cleaned in 0.3s - 69848 included, 30152 excluded
2025-12-14 21:42:53,928 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:42:53,928 [INFO] Batch 1: Inserted in 4.7s (parallel)
2025-12-14 21:42:53,928 [INFO] Batch 1 total time: 5.4s
2025-12-14 21:42:53,928 [INFO]
Processing batch 2/11 (rows 100001 to 200000)...
2025-12-14 21:42:54,141 [INFO] Starting to clean 100000 rows...
2025-12-14 21:42:54,390 [INFO] Processed 100000 rows...
2025-12-14 21:42:54,401 [INFO] Cleaning complete: 69610 included, 30390 excluded
2025-12-14 21:42:54,421 [INFO] Batch 2: Cleaned in 0.3s - 69610 included, 30390 excluded
2025-12-14 21:42:59,260 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:42:59,262 [INFO] Batch 2: Inserted in 4.8s (parallel)
2025-12-14 21:42:59,262 [INFO] Batch 2 total time: 5.3s
2025-12-14 21:42:59,264 [INFO]
Processing batch 3/11 (rows 200001 to 300000)...
2025-12-14 21:42:59,481 [INFO] Starting to clean 100000 rows...
2025-12-14 21:42:59,745 [INFO] Processed 100000 rows...
2025-12-14 21:42:59,754 [INFO] Cleaning complete: 70811 included, 29189 excluded
2025-12-14 21:42:59,772 [INFO] Batch 3: Cleaned in 0.3s - 70811 included, 29189 excluded
2025-12-14 21:43:04,513 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:04,517 [INFO] Batch 3: Inserted in 4.7s (parallel)
2025-12-14 21:43:04,517 [INFO] Batch 3 total time: 5.3s
2025-12-14 21:43:04,518 [INFO]
Processing batch 4/11 (rows 300001 to 400000)...
2025-12-14 21:43:04,717 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:04,973 [INFO] Processed 100000 rows...
2025-12-14 21:43:04,984 [INFO] Cleaning complete: 71946 included, 28054 excluded
2025-12-14 21:43:05,003 [INFO] Batch 4: Cleaned in 0.3s - 71946 included, 28054 excluded
2025-12-14 21:43:10,104 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:10,107 [INFO] Batch 4: Inserted in 5.1s (parallel)
2025-12-14 21:43:10,107 [INFO] Batch 4 total time: 5.6s
2025-12-14 21:43:10,107 [INFO]
Processing batch 5/11 (rows 400001 to 500000)...
2025-12-14 21:43:10,379 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:10,800 [INFO] Processed 100000 rows...
2025-12-14 21:43:10,809 [INFO] Cleaning complete: 73061 included, 26939 excluded
2025-12-14 21:43:10,836 [INFO] Batch 5: Cleaned in 0.4s - 73061 included, 26939 excluded
2025-12-14 21:43:15,209 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:15,211 [INFO] Batch 5: Inserted in 4.4s (parallel)
2025-12-14 21:43:15,212 [INFO] Batch 5 total time: 5.1s
2025-12-14 21:43:15,213 [INFO]
Processing batch 6/11 (rows 500001 to 600000)...
2025-12-14 21:43:15,485 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:15,922 [INFO] Processed 100000 rows...
2025-12-14 21:43:15,935 [INFO] Cleaning complete: 73651 included, 26349 excluded
2025-12-14 21:43:15,964 [INFO] Batch 6: Cleaned in 0.5s - 73651 included, 26349 excluded
2025-12-14 21:43:20,508 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:20,508 [INFO] Batch 6: Inserted in 4.5s (parallel)
2025-12-14 21:43:20,508 [INFO] Batch 6 total time: 5.3s
2025-12-14 21:43:20,516 [INFO]
Processing batch 7/11 (rows 600001 to 700000)...
2025-12-14 21:43:20,783 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:21,201 [INFO] Processed 100000 rows...
2025-12-14 21:43:21,215 [INFO] Cleaning complete: 72730 included, 27270 excluded
2025-12-14 21:43:21,240 [INFO] Batch 7: Cleaned in 0.4s - 72730 included, 27270 excluded
2025-12-14 21:43:25,971 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:25,983 [INFO] Batch 7: Inserted in 4.7s (parallel)
2025-12-14 21:43:26,005 [INFO] Batch 7 total time: 5.5s
2025-12-14 21:43:26,025 [INFO]
Processing batch 8/11 (rows 700001 to 800000)...
2025-12-14 21:43:26,399 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:26,693 [INFO] Processed 100000 rows...
2025-12-14 21:43:26,703 [INFO] Cleaning complete: 73708 included, 26292 excluded
2025-12-14 21:43:26,724 [INFO] Batch 8: Cleaned in 0.3s - 73708 included, 26292 excluded
2025-12-14 21:43:31,122 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:31,151 [INFO] Batch 8: Inserted in 4.4s (parallel)
2025-12-14 21:43:31,162 [INFO] Batch 8 total time: 5.1s
2025-12-14 21:43:31,179 [INFO]
Processing batch 9/11 (rows 800001 to 900000)...
2025-12-14 21:43:31,550 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:31,893 [INFO] Processed 100000 rows...
2025-12-14 21:43:31,903 [INFO] Cleaning complete: 74072 included, 25928 excluded
2025-12-14 21:43:31,927 [INFO] Batch 9: Cleaned in 0.4s - 74072 included, 25928 excluded
2025-12-14 21:43:36,322 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:36,328 [INFO] Batch 9: Inserted in 4.4s (parallel)
2025-12-14 21:43:36,328 [INFO] Batch 9 total time: 5.1s
2025-12-14 21:43:36,329 [INFO]
Processing batch 10/11 (rows 900001 to 1000000)...
2025-12-14 21:43:36,627 [INFO] Starting to clean 100000 rows...
2025-12-14 21:43:36,995 [INFO] Processed 100000 rows...
2025-12-14 21:43:37,012 [INFO] Cleaning complete: 73254 included, 26746 excluded
2025-12-14 21:43:37,034 [INFO] Batch 10: Cleaned in 0.4s - 73254 included, 26746 excluded
2025-12-14 21:43:40,759 [INFO] ✅ Inserted 100000 rows into clients_2025_apr_2025_original
2025-12-14 21:43:40,759 [INFO] Batch 10: Inserted in 3.7s (parallel)
2025-12-14 21:43:40,759 [INFO] Batch 10 total time: 4.4s
2025-12-14 21:43:40,759 [INFO]
Processing batch 11/11 (rows 1000001 to 1047527)...
2025-12-14 21:43:40,890 [INFO] Starting to clean 47527 rows...
2025-12-14 21:43:41,039 [INFO] Cleaning complete: 34611 included, 12916 excluded
2025-12-14 21:43:41,055 [INFO] Batch 11: Cleaned in 0.2s - 34611 included, 12916 excluded
2025-12-14 21:43:42,860 [INFO] ✅ Inserted 47527 rows into clients_2025_apr_2025_original
2025-12-14 21:43:42,860 [INFO] Batch 11: Inserted in 1.8s (parallel)
2025-12-14 21:43:42,860 [INFO] Batch 11 total time: 2.1s
2025-12-14 21:43:42,860 [INFO]
✓ Processing complete!
2025-12-14 21:43:42,862 [INFO] Total: 1,047,527 rows
2025-12-14 21:43:42,863 [INFO] Included: 757,302 rows
2025-12-14 21:43:42,863 [INFO] Excluded: 290,225 rows
2025-12-14 21:43:42,863 [INFO] Total processing time: 54.4s (0.9 minutes)
2025-12-14 21:43:42,863 [INFO] Average rate: 19272 rows/sec
2025-12-14 21:43:42,946 [INFO] 127.0.0.1 - - [14/Dec/2025 21:43:42] "POST /process/sheet2 HTTP/1.1" 200 -
```
![alt text](images3.png)

# Create Analytics - Execution Logs

## Create Analytics Execution Log

``` 
2025-12-14 21:56:46,767 [INFO] Creating analytics for sheet: sheet2
✓ Database connection established
2025-12-14 21:56:48,383 [INFO] Creating indexes on clients_2025_apr_2025_original...
2025-12-14 21:56:54,277 [INFO] ✅ Index created
2025-12-14 21:56:56,730 [INFO] ✅ Index created
2025-12-14 21:56:59,404 [INFO] ✅ Index created
2025-12-14 21:57:01,495 [INFO] ✅ Index created
2025-12-14 21:57:03,052 [INFO] ✅ Index created
2025-12-14 21:57:04,113 [INFO] ✅ Index created
2025-12-14 21:57:05,241 [INFO] ✅ Index created
2025-12-14 21:57:05,838 [INFO] ✅ Index created
2025-12-14 21:57:05,838 [INFO] ✅ All original table indexes created successfully
2025-12-14 21:57:06,428 [INFO] Creating analytics table: clients_2025_apr_2025_analytics
2025-12-14 21:57:29,487 [INFO] ✅ Analytics table created successfully
2025-12-14 21:57:41,754 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_name_year
2025-12-14 21:57:48,971 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_name_month
2025-12-14 21:57:58,801 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_name_day
2025-12-14 21:58:05,653 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_year_month
2025-12-14 21:58:11,728 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_year_day
2025-12-14 21:58:19,384 [INFO] ✅ Created duplicate group view: clients_2025_apr_2025_duplicates_month_day
2025-12-14 21:58:19,385 [INFO] Creating indexes on duplicate tables...
2025-12-14 21:58:21,482 [INFO] ✅ Index created
2025-12-14 21:58:22,809 [INFO] ✅ Index created
2025-12-14 21:58:24,409 [INFO] ✅ Index created
2025-12-14 21:58:25,001 [INFO] ✅ Index created
2025-12-14 21:58:25,661 [INFO] ✅ Index created
2025-12-14 21:58:26,250 [INFO] ✅ Index created
2025-12-14 21:58:26,250 [INFO] ✅ All duplicate table indexes created successfully
2025-12-14 21:58:28,080 [INFO] ✅ Created birth year chart table: clients_2025_apr_2025_chart_birthyear
2025-12-14 21:58:29,591 [INFO] ✅ Created birth month chart table: clients_2025_apr_2025_chart_birthmonth
2025-12-14 21:58:30,186 [INFO] Creating common names table: clients_2025_apr_2025_common_names
2025-12-14 21:58:32,459 [INFO] Creating indexes on clients_2025_apr_2025_common_names...
2025-12-14 21:58:34,300 [INFO] ✅ Common names table created successfully
2025-12-14 21:58:34,300 [INFO] ✅ Analytics created successfully for sheet2
✓ Database connection closed
2025-12-14 21:58:34,300 [INFO] 127.0.0.1 - - [14/Dec/2025 21:58:34] "POST /analytics/sheet2/create HTTP/1.1" 200 -
2025-12-14 21:58:34,315 [INFO] Getting analytics for sheet: sheet2
2025-12-14 21:58:34,317 [INFO] Getting birthyear chart data for sheet: sheet2
2025-12-14 21:58:34,319 [INFO] Getting name_year duplicates for sheet: sheet2
✓ Database connection established
✓ Database connection established
✓ Database connection established
✓ Database connection closed
2025-12-14 21:58:36,006 [INFO] 127.0.0.1 - - [14/Dec/2025 21:58:36] "GET /analytics/sheet2/charts/birthyear HTTP/1.1" 200 -
2025-12-14 21:58:36,849 [INFO] Analytics summary: {'unique_names': 183105, 'unique_birthdays': 2094, 'unique_name_year': 363700, 'unique_name_month': 183105, 'unique_name_day': 362138}
```

# Comparison Analytics - Execution Logs

## Process Execution Log

```
2025-12-14 22:02:49,417 [INFO] Creating comparison analytics between JAN and APR
2025-12-14 22:02:50,704 [INFO] ✓ Database connection established
2025-12-14 22:02:50,706 [INFO] ================================================================================
2025-12-14 22:02:50,706 [INFO] CREATING COMPARISON ANALYTICS
2025-12-14 22:02:50,707 [INFO] ================================================================================
2025-12-14 22:02:50,708 [INFO] Setting statement timeout to 10 minutes...
2025-12-14 22:02:51,310 [INFO] Verifying required tables exist...
2025-12-14 22:02:51,748 [INFO] ✓ Verified table exists: clients_2025_jan_2025_original
2025-12-14 22:02:51,958 [INFO] ✓ Verified table exists: clients_2025_jan_2025_common_names
2025-12-14 22:02:52,161 [INFO] ✓ Verified table exists: clients_2025_apr_2025_original
2025-12-14 22:02:52,360 [INFO] ✓ Verified table exists: clients_2025_apr_2025_common_names
2025-12-14 22:02:52,360 [INFO] Creating common names comparison table: clients_2025_comparison_common_names
2025-12-14 22:02:52,790 [INFO] Step 1/5: Creating temp tables for distinct names...
2025-12-14 22:02:58,302 [INFO] Step 2/5: Finding common names...
2025-12-14 22:03:08,608 [INFO] Step 3/5: Calculating frequencies...
2025-12-14 22:03:13,347 [INFO] Step 4/5: Getting top 80% information...
2025-12-14 22:03:16,706 [INFO] Step 5/5: Creating final comparison table...
2025-12-14 22:03:18,978 [INFO] Cleaning up temporary tables...
2025-12-14 22:03:23,794 [INFO] ✅ Created common names table: clients_2025_comparison_common_names
2025-12-14 22:03:23,794 [INFO] Creating unique JAN names table: clients_2025_comparison_unique_jan
2025-12-14 22:03:24,818 [INFO] Step 1/4: Creating temp table with distinct JAN names...
2025-12-14 22:03:27,206 [INFO] Step 2/4: Creating temp table with distinct APR names...
2025-12-14 22:03:29,629 [INFO] Step 3/4: Finding names unique to JAN...
2025-12-14 22:03:31,234 [INFO] Step 4/4: Creating final unique JAN table with all records...
2025-12-14 22:03:48,063 [INFO] ✅ Created unique JAN names table: clients_2025_comparison_unique_jan
2025-12-14 22:03:48,064 [INFO] Creating unique APR names table: clients_2025_comparison_unique_apr
2025-12-14 22:03:48,656 [INFO] Step 1/4: Creating temp table with distinct JAN names...
2025-12-14 22:03:51,820 [INFO] Step 2/4: Creating temp table with distinct APR names...
2025-12-14 22:03:54,751 [INFO] Step 3/4: Finding names unique to APR...
2025-12-14 22:03:56,296 [INFO] Step 4/4: Creating final unique APR table with all records...
2025-12-14 22:04:09,416 [INFO] ✅ Created unique APR names table: clients_2025_comparison_unique_apr
2025-12-14 22:04:09,417 [INFO] Creating comparison summary table: clients_2025_comparison_summary
2025-12-14 22:04:16,733 [INFO] ✅ Created comparison summary table: clients_2025_comparison_summary
2025-12-14 22:04:16,733 [INFO] Creating indexes on comparison tables...
2025-12-14 22:04:26,252 [INFO] ✅ All comparison indexes created successfully
2025-12-14 22:04:26,859 [INFO] ================================================================================
2025-12-14 22:04:26,859 [INFO] ✅ COMPARISON ANALYTICS COMPLETED SUCCESSFULLY
2025-12-14 22:04:26,859 [INFO] ================================================================================
2025-12-14 22:04:26,859 [INFO] ✅ Comparison analytics created successfully
2025-12-14 22:04:26,859 [INFO] ✓ Database connection closed
2025-12-14 22:04:26,862 [INFO] 127.0.0.1 - - [14/Dec/2025 22:04:26] "POST /comparison/create HTTP/1.1" 200 -
2025-12-14 22:04:26,876 [INFO] Getting comparison summary
2025-12-14 22:04:28,070 [INFO] ✓ Database connection established
2025-12-14 22:04:28,463 [INFO] ✓ Database connection closed
```