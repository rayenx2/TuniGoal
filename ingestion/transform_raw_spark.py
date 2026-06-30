from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth, dayofweek, date_format, hash, abs, to_date


# 1️⃣ Create Spark session
spark = SparkSession.builder \
    .appName("FootballDataPipeline_Enterprise") \
    .config("spark.jars", "/opt/airflow/jars/postgresql-42.7.10.jar") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# PostgreSQL connection variables
postgres_url = "jdbc:postgresql://tunigoal-dw:5432/tunigoal_db"
postgres_props = {
    "user": "admin",
    "password": "admin123",
    "driver": "org.postgresql.Driver"
}

# 2️⃣ Read Data FROM Postgres Staging Table
print("Extracting data from staging table...")
stg_df = spark.read.jdbc(url=postgres_url, table="public.raw_matches", properties=postgres_props)

# -------------------------
# 🛡️ DATA QUALITY GATES 
# -------------------------
print("Executing Data Quality Checks...")

# 1. Drop absolute duplicates based on the primary key
stg_df = stg_df.dropDuplicates(["match_id"])

# 2. Drop rows where critical fields are missing (Null handling)
stg_df = stg_df.dropna(subset=["match_id", "home_team", "away_team", "match_date"])

# 3. Business Logic Validation (Goals cannot be negative)
stg_df = stg_df.filter((col("home_goals") >= 0) & (col("away_goals") >= 0))


# -------------------------
# ⭐ BUILD DIMENSION TABLES
# -------------------------
print("Building Dimension Tables...")

# --- dim_teams (Using Deterministic Hashing) ---
home_teams = stg_df.select(col("home_team").alias("team_name"))
away_teams = stg_df.select(col("away_team").alias("team_name"))

# By using abs(hash()), "Raja CA" will ALWAYS generate the exact same integer ID
dim_teams = home_teams.union(away_teams) \
    .distinct() \
    .withColumn("team_id", abs(hash(col("team_name"))))

dim_teams.write.jdbc(url=postgres_url, table="public.dim_teams", mode="overwrite", properties=postgres_props)

# --- dim_leagues ---
dim_leagues = stg_df.select(col("league_id")).distinct()
dim_leagues.write.jdbc(url=postgres_url, table="public.dim_leagues", mode="overwrite", properties=postgres_props)

dim_dates = stg_df.select(to_date(col("match_date")).alias("pure_date")) \
    .distinct() \
    .withColumn("date_id", date_format("pure_date", "yyyyMMdd").cast("int")) \
    .withColumn("year", year("pure_date")) \
    .withColumn("month", month("pure_date")) \
    .withColumn("day", dayofmonth("pure_date")) \
    .withColumn("weekday", dayofweek("pure_date"))

dim_dates.write.jdbc(url=postgres_url, table="public.dim_dates", mode="overwrite", properties=postgres_props)


# -------------------------
# ⭐ BUILD FACT TABLE (Incremental Load)
# -------------------------
print("Building Fact Table...")

new_fact_matches = stg_df.alias("stg") \
    .join(dim_teams.alias("t1"), col("stg.home_team") == col("t1.team_name")) \
    .join(dim_teams.alias("t2"), col("stg.away_team") == col("t2.team_name")) \
    .withColumn("date_id", date_format("stg.match_date", "yyyyMMdd").cast("int")) \
    .select(
        col("stg.match_id"),
        col("date_id"),           # Generated dynamically, no join to dim_dates needed!
        col("stg.league_id"),
        col("t1.team_id").alias("home_team_id"),
        col("t2.team_id").alias("away_team_id"),
        col("stg.home_goals"),
        col("stg.away_goals")
    )

# 🔄 The Delta Load Pattern: Check what is already in the database
try:
    existing_facts = spark.read.jdbc(url=postgres_url, table="public.fact_matches", properties=postgres_props).select("match_id")
    
    # Left Anti Join: Keep ONLY records from new_fact_matches that DO NOT exist in existing_facts
    final_fact_matches = new_fact_matches.join(existing_facts, on="match_id", how="left_anti")
    print(f"Found existing data. Appending {final_fact_matches.count()} new match records.")
    
except Exception as e:
    # If the table doesn't exist yet (first run), just load everything
    print("Fact table does not exist yet. Performing initial load.")
    final_fact_matches = new_fact_matches

# 🚨 CHANGE TO APPEND MODE
final_fact_matches.write.jdbc(
    url=postgres_url,
    table="public.fact_matches",
    mode="append",  # Now safe to append because duplicates are filtered out!
    properties=postgres_props
)

print("✅ Star schema successfully updated with incremental load!")
spark.stop()