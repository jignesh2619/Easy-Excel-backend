# 📊 How to Get Dashboards & Charts

## Overview

EasyExcel can generate **charts and visualizations** from your Excel/CSV data. Here's how to get them!

## 🎯 What You Can Get

1. **Charts** (PNG images)
   - Bar charts
   - Line charts
   - Pie charts

2. **Processed Excel Files**
   - Cleaned data
   - Grouped/summarized data
   - Ready for dashboard tools

## 🚀 How to Get Charts/Dashboards

### Step 1: Upload Your File

Upload an Excel or CSV file through:
- Frontend: http://localhost:3000
- Or use the API directly

### Step 2: Use the Right Prompt

To get charts, include chart/dashboard keywords in your prompt:

#### Examples of Prompts that Generate Charts:

✅ **"Group by Region and sum Revenue, create a bar chart"**
- Groups data by Region
- Sums Revenue
- Creates bar chart

✅ **"Show me sales by month with a line chart"**
- Groups by month
- Creates line chart

✅ **"Create a dashboard showing revenue by category as a pie chart"**
- Groups by category
- Creates pie chart

✅ **"Summarize sales data and generate a bar chart"**
- Summarizes data
- Creates bar chart

✅ **"Group by product and show total sales in a bar chart"**
- Groups by product
- Creates bar chart

## 📝 Prompt Templates for Dashboards

### Sales Dashboard:
```
"Group by Region and sum Revenue, then create a bar chart showing sales by region"
```

### Time Series Dashboard:
```
"Show monthly sales trend with a line chart"
```

### Category Breakdown:
```
"Create a pie chart showing revenue distribution by category"
```

### KPI Dashboard:
```
"Group by quarter, sum revenue and quantity, create a bar chart with both metrics"
```

## 🎨 Chart Types Available

### 1. Bar Chart
**Best for:** Comparing categories, groups
**Example prompt:** 
```
"Group by Category and sum Sales, create a bar chart"
```

### 2. Line Chart
**Best for:** Trends over time
**Example prompt:**
```
"Show monthly revenue trend with a line chart"
```

### 3. Pie Chart
**Best for:** Proportions, percentages
**Example prompt:**
```
"Create a pie chart showing revenue by region"
```

## 🔄 How It Works

1. **You upload a file** (Excel/CSV)
2. **You enter a prompt** (e.g., "Group by Region, sum Revenue, create bar chart")
3. **AI interprets** your prompt and creates an action plan
4. **Backend processes** your data:
   - Groups/summarizes data
   - Creates processed Excel file
   - Generates chart (if requested)
5. **You download** both:
   - Processed Excel file
   - Chart image (PNG)

## 📥 Downloading Charts

After processing, you'll get:

### From Frontend:
- ✅ **Processed Excel file** - Downloads automatically
- ✅ **Chart image** - Click "Download Chart" button

### From API Response:
```json
{
  "status": "success",
  "processed_file_url": "/download/processed_file.xlsx",
  "chart_url": "/download/charts/chart_20250115_120000.png",
  "summary": [...]
}
```

### Direct Download URLs:
- **Processed file:** `http://localhost:8000/download/processed_file.xlsx`
- **Chart:** `http://localhost:8000/download/charts/chart_20250115_120000.png`

## 💡 Tips for Better Dashboards

### 1. Be Specific About Chart Type
✅ Good: "Create a bar chart showing sales by region"
❌ Bad: "Show me data" (no chart type specified)

### 2. Specify Grouping
✅ Good: "Group by Category and sum Revenue, create bar chart"
❌ Bad: "Create chart" (AI won't know what to group)

### 3. Request Multiple Metrics
✅ Good: "Group by Region, show sum of Revenue and count of Orders, create bar chart"

### 4. Mention Time Periods
✅ Good: "Show monthly revenue trend with line chart"
❌ Bad: "Show trends" (too vague)

## 🔧 Advanced: Multiple Charts

Currently, you get **one chart per processing**. To get multiple charts:

1. **Process file once** to get first chart
2. **Process again** with different prompt for second chart
3. **Combine in Excel** or use dashboard tools

## 📊 Using Processed Data in Dashboard Tools

Your processed Excel file can be imported into:

- **Power BI** - Import the processed Excel file
- **Tableau** - Connect to processed Excel file
- **Google Sheets** - Upload processed Excel file
- **Excel** - Open processed Excel file directly

## 🐛 Troubleshooting

### No Chart Generated?

1. **Check your prompt** - Did you ask for a chart?
2. **Check summary** - See what actions were taken
3. **Check data** - Is there data to visualize?

### Chart Looks Wrong?

1. **Be more specific** - Which columns to use
2. **Check data format** - Ensure numeric columns exist
3. **Try different chart type** - Bar vs Line vs Pie

## 📋 Example Workflow

1. **Upload:** `sales_data.xlsx`
2. **Prompt:** `"Group by Region and sum Revenue, create a bar chart"`
3. **Wait:** Processing takes a few seconds
4. **Download:** 
   - `processed_sales_data.xlsx` (grouped data)
   - `chart_20250115_120000.png` (bar chart)
5. **Use:** Import both into your dashboard tool!

## ✅ Quick Reference

| What You Want | Prompt Example |
|--------------|----------------|
| Bar Chart | "Group by X, sum Y, create bar chart" |
| Line Chart | "Show monthly trend with line chart" |
| Pie Chart | "Create pie chart showing revenue by category" |
| Sales Dashboard | "Group by Region, sum Revenue, create bar chart" |
| Time Series | "Show monthly revenue with line chart" |
| Summary Stats | "Show summary statistics for Revenue and Quantity" |

---

**Ready to create dashboards? Upload your file and try these prompts!** 🚀



