import importlib.util
import logging

from kedro.framework.hooks import hook_impl

# Check if pyspark is available
pyspark_available = importlib.util.find_spec("pyspark") is not None

# Only import pyspark if it's available
if pyspark_available:
    from pyspark import SparkConf
    from pyspark.sql import SparkSession
else:
    logging.warning("PySpark not found. SparkHooks will be disabled.")


class SparkHooks:
    @hook_impl
    def after_context_created(self, context) -> None:
        """Initialises a SparkSession using the config
        defined in project's conf folder.
        """
        # Skip if pyspark is not available
        if not pyspark_available:
            logging.warning("Skipping SparkSession initialization: PySpark not available")
            return

        # Load the spark configuration in spark.yaml using the config loader
        parameters = context.config_loader["spark"]
        spark_conf = SparkConf().setAll(parameters.items())

        # Initialise the spark session
        spark_session_conf = (
            SparkSession.builder.appName(context.project_path.name)
            .enableHiveSupport()
            .config(conf=spark_conf)
        )
        _spark_session = spark_session_conf.getOrCreate()
        _spark_session.sparkContext.setLogLevel("WARN")
