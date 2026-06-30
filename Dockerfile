FROM apache/airflow:2.8.1

# 2. Switch to the root user to install system packages
USER root

# 3. Install Java (OpenJDK 17)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         default-jre-headless \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 4. Set the JAVA_HOME environment variable so Spark can find it
ENV JAVA_HOME=/usr/lib/jvm/default-java

# 5. Switch back to the airflow user for security
USER airflow

# 6. Install the PySpark Python library
RUN pip install --no-cache-dir "pyspark==3.5.0" requests