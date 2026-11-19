#!/usr/bin/env python
# coding: utf-8

# # Exploratory Data Analysis
# Understanding the dataset to explore how the data is present in the database and if there is a need of creating some aggregated tables that can help with:
# - Vendor selection for profitability
# - Product Pricing Optimization

# In[1]:


import sqlite3
import pandas as pd


# In[2]:


# creating database connection
conn = sqlite3.connect('inventory.db')


# In[3]:


# checking tables present in the database
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'",conn)
tables


# In[4]:


# exploring what type of data available in the tables
for table in tables['name']:
    print('-'*50,f'{table}','-'*50)
    print('Count of records:',pd.read_sql_query(f"select count(*) as count from {table}",conn)['count'].values[0])
    display(pd.read_sql_query(f"select * from {table} limit 5",conn))


# In[5]:


# choosing one vendor and filtering the different tables 
purchases = pd.read_sql_query("select * from purchases where VendorNumber = 4466",conn)
purchases


# In[6]:


purchase_prices = pd.read_sql_query("""select * from purchase_prices where VendorNumber = 4466""",conn)
purchase_prices


# In[7]:


vendor_invoice = pd.read_sql_query("""select * from vendor_invoice where VendorNumber = 4466""",conn)
vendor_invoice


# In[8]:


sales = pd.read_sql_query("""select * from sales where VendorNo = 4466""",conn)
sales


# In[9]:


purchases.groupby(["Brand","PurchasePrice"])[["Quantity","Dollars"]].sum()


# In[10]:


purchases.groupby(["PONumber"])[["Quantity","Dollars"]].sum()


# In[11]:


sales.groupby("Brand")[['SalesQuantity','SalesDollars','SalesPrice','ExciseTax']].sum()


# - The purchases table contains actual purchase data, including the date of purchase, products (brands) purchased by vendors, the amount paid (in dollars), and the quantity purchased.
# - The purchase price column is derived from the purchase_prices table, which provides product-wise actual and purchase prices. The combination of vendor and brand is unique in this table.
# - The vendor_invoice table aggregates data from the purchases table, summarizing quantity and dollar amounts, along with an additional column for freight. This table maintains uniqueness based on vendor and PO number.
# - The sales table captures actual sales transactions, detailing the brands purchased by vendors, the quantity sold, the selling price, and the revenue earned.
# ---
# As the data that we need for analysis is distributed in different tables, we need to create a summary table containing:
# - purchase transactions made by vendors
# - sales transaction data
# - freight costs for each vendor
# - actual product prices from vendors

# In[12]:


freight_summary = pd.read_sql_query("""SELECT 
    VendorNumber, 
    SUM(Freight) as FreightCost 
FROM vendor_invoice 
GROUP BY VendorNumber""", conn)
freight_summary


# In[13]:


purchase_summary = pd.read_sql_query("""SELECT 
    p.VendorNumber,
    p.VendorName,
    p.Brand,
    p.Description,
    p.PurchasePrice,
    pp.Price as ActualPrice,
    pp.Volume,
    SUM(p.Quantity) AS TotalPurchaseQuantity,
    SUM(p.Dollars) AS TotalPurchaseDollars
FROM purchases p
JOIN purchase_prices pp
    ON p.Brand = pp.Brand
WHERE p.PurchasePrice > 0
GROUP BY p.VendorNumber,p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
ORDER BY TotalPurchaseDollars
""",conn)
purchase_summary


# In[14]:


sales_summary = pd.read_sql_query("""SELECT 
    VendorNo,
    Brand,
    SUM(SalesQuantity) AS TotalSalesQuantity,
    SUM(SalesDollars) AS TotalSalesDollars,
    SUM(SalesPrice) AS TotalSalesPrice,
    SUM(ExciseTax) AS TotalExciseTax
FROM sales
GROUP BY VendorNo, Brand""",conn)
sales_summary


# In[15]:


# merging all the summary table to create an aggregated summary table for further analysis
vendor_sales_summary = pd.read_sql_query("""WITH FreightSummary AS (
    SELECT 
        VendorNumber, 
        SUM(Freight) AS FreightCost 
    FROM vendor_invoice 
    GROUP BY VendorNumber
), 

PurchaseSummary AS (
    SELECT 
        p.VendorNumber,
        p.VendorName,
        p.Brand,
        p.Description,
        p.PurchasePrice,
        pp.Price AS ActualPrice,
        pp.Volume,
        SUM(p.Quantity) AS TotalPurchaseQuantity,
        SUM(p.Dollars) AS TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp
        ON p.Brand = pp.Brand
    WHERE p.PurchasePrice > 0
    GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Price, pp.Volume
), 

SalesSummary AS (
    SELECT 
        VendorNo,
        Brand,
        SUM(SalesQuantity) AS TotalSalesQuantity,
        SUM(SalesDollars) AS TotalSalesDollars,
        SUM(SalesPrice) AS TotalSalesPrice,
        SUM(ExciseTax) AS TotalExciseTax
    FROM sales
    GROUP BY VendorNo, Brand
) 

SELECT 
    ps.VendorNumber,
    ps.VendorName,
    ps.Brand,
    ps.Description,
    ps.PurchasePrice,
    ps.ActualPrice,
    ps.Volume,
    ps.TotalPurchaseQuantity,
    ps.TotalPurchaseDollars,
    ss.TotalSalesQuantity,
    ss.TotalSalesDollars,
    ss.TotalSalesPrice,
    ss.TotalExciseTax,
    fs.FreightCost
FROM PurchaseSummary ps
LEFT JOIN SalesSummary ss 
    ON ps.VendorNumber = ss.VendorNo 
    AND ps.Brand = ss.Brand
LEFT JOIN FreightSummary fs 
    ON ps.VendorNumber = fs.VendorNumber
ORDER BY ps.TotalPurchaseDollars DESC""",conn)


# In[16]:


vendor_sales_summary.columns


# This query generates a vendor-wise sales and purchase summary, which is valuable for:
# 
# **Performance Optimization:**
# - The query involves heavy joins and aggregations on large datasets like sales and purchases.
# - Storing the pre-aggregated results avoids repeated expensive computations.
# - Helps in analyzing sales, purchases, and pricing for different vendors and brands.
# - Future Benefits of Storing this data for faster Dashboarding & Reporting.
# - Instead of running expensive queries each time, dashboards can fetch data quickly from vendor_sales_summary.
# 
# Let's clean the data if there is any inconsistencies. 

# In[17]:


vendor_sales_summary.dtypes


# In[18]:


vendor_sales_summary['Volume'].unique()


# In[19]:


vendor_sales_summary['VendorName'].unique()


# - The Volume is a numerical column but having object datatype.
# - There are some products that are not sold, so having missing values.
# - There are white spaces in the categorical columns.

# In[20]:


# creating new columns for better analysis
vendor_sales_summary['GrossProfit'] = vendor_sales_summary['TotalSalesDollars'] - vendor_sales_summary['TotalPurchaseDollars']
vendor_sales_summary['ProfitMargin'] = (vendor_sales_summary['GrossProfit'] / vendor_sales_summary['TotalSalesDollars'])*100
vendor_sales_summary['StockTurnover'] = vendor_sales_summary['TotalSalesQuantity'] / vendor_sales_summary['TotalPurchaseQuantity']
vendor_sales_summary['SalesToPurchaseRatio'] = vendor_sales_summary['TotalSalesDollars'] / vendor_sales_summary['TotalPurchaseDollars']


# In[21]:


# changing datatype to float
vendor_sales_summary['Volume'] = vendor_sales_summary['Volume'].astype('float')

# filling missing value with 0
vendor_sales_summary.fillna(0,inplace = True)

# removing spaces from categorical columns
vendor_sales_summary['VendorName'] = vendor_sales_summary['VendorName'].str.strip()
vendor_sales_summary['Description'] = vendor_sales_summary['Description'].str.strip()


# ####  Saving cleaned data into database

# In[22]:


cursor = conn.cursor()


# In[23]:


# only runs once 
cursor.execute("""CREATE TABLE vendor_sales_summary (
    VendorNumber INT,
    VendorName VARCHAR(100),
    Brand INT,
    Description VARCHAR(100),
    PurchasePrice DECIMAL(10,2),
    ActualPrice DECIMAL(10,2),
    Volume INT,
    TotalPurchaseQuantity INT,
    TotalPurchaseDollars DECIMAL(15,2),
    TotalSalesQuantity INT,
    TotalSalesDollars DECIMAL(15,2),
    TotalSalesPrice DECIMAL(15,2),
    TotalExciseTax DECIMAL(15,2),
    FreightCost DECIMAL(15,2),
    GrossProfit DECIMAL(15,2),
    ProfitMargin DECIMAL(15,2),
    StockTurnover DECIMAL(15,2),
    SalesToPurchaseRatio DECIMAL(15,2),
    PRIMARY KEY (VendorNumber, Brand)
);
""")


# In[ ]:


vendor_sales_summary.to_sql('vendor_sales_summary', conn, if_exists = 'replace', index = False )


# In[ ]:


pd.read_sql_query("select * from vendor_sales_summary",conn)


# In[ ]:





# In[ ]:




