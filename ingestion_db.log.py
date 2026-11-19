#!/usr/bin/env python
# coding: utf-8

# In[7]:


# Use this script to save csv files into database with their filename as tablename
import pandas as pd
import os
from sqlalchemy import create_engine
import logging
import time

# Logging configuration
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

# SQLite connection
engine = create_engine("sqlite:///inventory.db")


def ingest_db(df, table_name, engine):
    """Ingest dataframe into database table."""
    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False
    )


def load_raw_data():
    """Load CSV files and ingest into database."""

    start = time.time()

    for file in os.listdir("."):

        if file.lower().endswith(".csv"):

            df = pd.read_csv(file)

            table_name = os.path.splitext(file)[0].lower()

            logging.info(f"Ingesting {file} into database")

            ingest_db(df, table_name, engine)

            print(f"Successfully ingested: {table_name}")

    end = time.time()

    total_time = (end - start) / 60

    logging.info("--------------Ingestion Complete------------")
    logging.info(f"Total Time Taken: {total_time:.2f} minutes")

    print(f"\nTotal Time Taken: {total_time:.2f} minutes")


if __name__ == "__main__":
    load_raw_data()


# In[3]:


from sqlalchemy import inspect

inspector = inspect(engine)

print(inspector.get_table_names())


# In[4]:


for table in inspector.get_table_names():

    df = pd.read_sql(
        f'SELECT COUNT(*) AS total_records FROM "{table}"',
        engine
    )

    print(table, df.iloc[0, 0])


# In[ ]:





# In[ ]:




